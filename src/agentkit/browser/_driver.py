"""Provision a Chrome-family driver that matches the browser in use.

Detection (the running browser over CDP, or the installed binary) feeds a cache
lookup, and a miss is filled by downloading the matching driver from Chrome for
Testing. :func:`ensure_chromedriver` is idempotent and serialized across processes by
a cache lock; :func:`prefetch_chromedriver` runs the same work in a daemon thread so a
download can overlap the caller's other work instead of blocking it.
"""

from __future__ import annotations

import json
import logging
import os
import platform
import re
import subprocess
import sys
import threading
import time
import urllib.request
import zipfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

try:  # POSIX file locking; other platforms fall back to the in-process lock.
    import fcntl
except ImportError:  # pragma: no cover - Windows
    fcntl = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

_BRAVE_PATH_MACOS = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
_IS_MACOS = sys.platform == "darwin"

_BROWSER_VERSION_RE = re.compile(r"(?:Chrome|Chromium|Brave Browser)[/ ](\d+)")
_DRIVER_VERSION_RE = re.compile(r"ChromeDriver\s+(\d+)")

_CfT_LAST_KNOWN_GOOD_URL = (
    "https://googlechromelabs.github.io/chrome-for-testing/"
    "last-known-good-versions-with-downloads.json"
)
_CfT_ALL_VERSIONS_URL = (
    "https://googlechromelabs.github.io/chrome-for-testing/"
    "known-good-versions-with-downloads.json"
)
_SELENIUM_CACHE_DEFAULT = Path.home() / ".cache" / "selenium"

# Bounds for the one-time driver download after a browser upgrade. Selenium
# Manager's own network timeout defaults to 300 s per request, which is why a
# stalled download used to block an attach for minutes with no output. The metadata
# fetch is quick; the zip is a few megabytes and a slow link can legitimately need
# minutes, so its budget is generous but finite and progress is logged so the wait is
# never silent. Override with ``AGENTKIT_DRIVER_DOWNLOAD_TIMEOUT_S``.
_CFT_METADATA_TIMEOUT_S = 60.0
_CFT_DOWNLOAD_TIMEOUT_S = 600.0

_PREFETCH_GUARD = threading.Lock()
_PREFETCH: dict[str, "DriverPrefetch"] = {}


def _selenium_cache_root() -> Path:
    return Path(os.environ.get("SE_CACHE_PATH") or _SELENIUM_CACHE_DEFAULT)


def _driver_binary_name() -> str:
    return "chromedriver.exe" if sys.platform == "win32" else "chromedriver"


def chromedriver_major(path: str, timeout_s: float = 10.0) -> str | None:
    """Major version of the chromedriver at ``path``, or ``None`` when unusable."""
    try:
        proc = subprocess.run(
            [path, "--version"], capture_output=True, text=True, timeout=timeout_s
        )
    except Exception:
        return None
    match = _DRIVER_VERSION_RE.search(proc.stdout or "")
    return match.group(1) if match else None


def _version_major(text: str) -> str | None:
    match = _BROWSER_VERSION_RE.search(text or "")
    return match.group(1) if match else None


def browser_major_from_cdp(address: str, timeout_s: float = 2.0) -> str | None:
    """Major version of the browser listening on ``address`` via the CDP endpoint."""
    try:
        request = urllib.request.Request(f"http://{address}/json/version")
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return _version_major(str(payload.get("Browser", "")))
    except Exception:
        return None


def browser_major_from_binary(binary: str, timeout_s: float = 10.0) -> str | None:
    """Major version reported by a browser binary's ``--version`` output."""
    try:
        proc = subprocess.run(
            [binary, "--version"], capture_output=True, text=True, timeout=timeout_s
        )
    except Exception:
        return None
    return _version_major(proc.stdout or "")


def resolve_browser_major(
    *, debugger_address: str | None = None, binary: str | None = None
) -> str | None:
    """Major version to match a driver against.

    The running browser (CDP) wins: a Brave that auto-updated but has not restarted
    still runs the older Chromium, and the driver must match what is running. The
    installed binary is the fallback, which lets a prewarm run with no browser open.
    """
    if debugger_address:
        major = browser_major_from_cdp(debugger_address)
        if major:
            return major
    candidate = binary or (
        _BRAVE_PATH_MACOS if Path(_BRAVE_PATH_MACOS).exists() else None
    )
    if candidate:
        return browser_major_from_binary(candidate)
    return None


def find_cached_chromedriver(
    major: str, *, cache_root: Path | None = None
) -> str | None:
    """Path to a cached chromedriver matching ``major``, or ``None``."""
    root = cache_root or _selenium_cache_root()
    binary_name = _driver_binary_name()
    for candidate in sorted(root.glob(f"chromedriver/*/*/{binary_name}")):
        if candidate.parent.name.split(".")[0] != major:
            continue
        if chromedriver_major(str(candidate)) == major:
            return str(candidate)
    return None


@contextmanager
def _cache_lock() -> Iterator[None]:
    """Serialize driver installs across threads and processes."""
    root = _selenium_cache_root()
    root.mkdir(parents=True, exist_ok=True)
    lock_path = root / ".agentkit-driver.lock"
    with open(lock_path, "w") as handle:
        if fcntl is not None:
            fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(handle, fcntl.LOCK_UN)


def _cft_platform_key() -> str | None:
    """Chrome for Testing download platform for this machine, or ``None``."""
    machine = platform.machine().lower()
    if sys.platform == "darwin":
        return "mac-arm64" if machine == "arm64" else "mac-x64"
    if sys.platform.startswith("linux"):
        return "linux-arm64" if machine in ("aarch64", "arm64") else "linux64"
    if sys.platform == "win32":
        return "win64" if sys.maxsize > 2**32 else "win32"
    return None


def _cft_driver_url(entry: dict, platform_key: str) -> str | None:
    for download in entry.get("downloads", {}).get("chromedriver", []):
        if download.get("platform") == platform_key:
            return download.get("url")
    return None


def _fetch_json(url: str, timeout_s: float) -> dict:
    request = urllib.request.Request(url)
    with urllib.request.urlopen(request, timeout=timeout_s) as response:
        return json.loads(response.read().decode("utf-8"))


def _http_download(url: str, dest: Path, timeout_s: float) -> None:
    """Stream ``url`` to ``dest``, failing once ``timeout_s`` elapses in total.

    ``urllib``'s socket timeout is per read, so a slow but steady transfer would
    otherwise run past the budget; the loop enforces a wall-clock deadline and logs
    progress so a long download never looks like a hang.
    """
    start = time.monotonic()
    deadline = start + timeout_s
    last_log = start
    received = 0
    request = urllib.request.Request(url)
    with (
        urllib.request.urlopen(request, timeout=min(timeout_s, 30.0)) as response,
        open(dest, "wb") as target,
    ):
        while True:
            now = time.monotonic()
            if now >= deadline:
                raise TimeoutError(f"download from {url} exceeded {timeout_s:.0f}s")
            chunk = response.read(1 << 16)
            if not chunk:
                break
            target.write(chunk)
            received += len(chunk)
            if now - last_log >= 15:
                last_log = now
                logger.info(
                    "chromedriver download: %.1f MB so far (%.0fs elapsed)",
                    received / 1_000_000,
                    now - start,
                )


def _chromedriver_download(major: str, timeout_s: float) -> tuple[str, str] | None:
    """Return ``(version, url)`` of a Chrome for Testing chromedriver for ``major``.

    The small last-known-good file covers the stable/beta/dev/canary heads, which is
    where a just-updated browser lands; the full list is a fallback for older majors.
    """
    platform_key = _cft_platform_key()
    if platform_key is None:
        return None
    try:
        channels = _fetch_json(_CfT_LAST_KNOWN_GOOD_URL, timeout_s).get("channels", {})
        for channel in ("Stable", "Beta", "Dev", "Canary"):
            entry = channels.get(channel) or {}
            version = str(entry.get("version", ""))
            url = _cft_driver_url(entry, platform_key)
            if version.split(".")[0] == major and url:
                return version, url
    except Exception:
        pass
    try:
        versions = _fetch_json(_CfT_ALL_VERSIONS_URL, timeout_s).get("versions", [])
        for entry in reversed(versions):
            version = str(entry.get("version", ""))
            url = _cft_driver_url(entry, platform_key)
            if version.split(".")[0] == major and url:
                return version, url
    except Exception:
        pass
    return None


def _install_chromedriver(version: str, url: str, timeout_s: float) -> str:
    """Download a chromedriver zip into the Selenium cache and return its path."""
    platform_key = _cft_platform_key() or ""
    binary_name = _driver_binary_name()
    dest_dir = _selenium_cache_root() / "chromedriver" / platform_key / version
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / binary_name
    archive_path = dest_dir / f".{binary_name}.download"
    try:
        _http_download(url, archive_path, timeout_s)
        with zipfile.ZipFile(archive_path) as archive:
            member = next(
                (
                    name
                    for name in archive.namelist()
                    if name.endswith(f"/{binary_name}") or name == binary_name
                ),
                None,
            )
            if member is None:
                raise RuntimeError(
                    f"chromedriver binary not found in archive from {url}"
                )
            with archive.open(member) as source, open(dest, "wb") as target:
                target.write(source.read())
    finally:
        archive_path.unlink(missing_ok=True)
    dest.chmod(0o755)
    if _IS_MACOS:
        subprocess.run(
            ["xattr", "-d", "com.apple.quarantine", str(dest)],
            capture_output=True,
        )
    return str(dest)


def _download_budget_s() -> float:
    raw = os.environ.get("AGENTKIT_DRIVER_DOWNLOAD_TIMEOUT_S")
    if raw:
        try:
            return max(1.0, float(raw))
        except ValueError:
            pass
    return _CFT_DOWNLOAD_TIMEOUT_S


def _download_matching_driver(major: str, timeout_s: float) -> str:
    """Fetch the chromedriver matching ``major`` from Chrome for Testing."""
    found = _chromedriver_download(major, _CFT_METADATA_TIMEOUT_S)
    if found is None:
        raise RuntimeError(
            f"No Chrome for Testing chromedriver found for browser major {major}"
        )
    version, url = found
    return _install_chromedriver(version, url, timeout_s)


def _ensure_blocking(major: str, *, timeout_s: float | None = None) -> str:
    """Cache lookup then, under a cross-process lock, a bounded download."""
    cached = find_cached_chromedriver(major)
    if cached:
        return cached
    with _cache_lock():
        cached = find_cached_chromedriver(major)
        if cached:
            return cached
        budget = _download_budget_s() if timeout_s is None else timeout_s
        logger.warning(
            "No cached chromedriver for browser %s; downloading from Chrome for "
            "Testing (up to %.0fs, once per browser upgrade)…",
            major,
            budget,
        )
        return _download_matching_driver(major, budget)


class DriverPrefetch:
    """Handle for a background :func:`ensure_chromedriver` run."""

    def __init__(self, major: str, *, timeout_s: float | None = None) -> None:
        self.major = major
        self._timeout_s = timeout_s
        self._path: str | None = None
        self._error: BaseException | None = None
        self._done = threading.Event()
        self._thread = threading.Thread(
            target=self._run, name=f"chromedriver-prefetch-{major}", daemon=True
        )

    def _run(self) -> None:
        try:
            self._path = _ensure_blocking(self.major, timeout_s=self._timeout_s)
        except BaseException as exc:  # noqa: BLE001 - surfaced via result()
            self._error = exc
        finally:
            self._done.set()

    @property
    def running(self) -> bool:
        return not self._done.is_set()

    def start(self) -> "DriverPrefetch":
        self._thread.start()
        return self

    def result(self, timeout: float | None = None) -> str:
        if not self._done.wait(timeout):
            raise TimeoutError(
                f"chromedriver prefetch for {self.major} is still running"
            )
        if self._error is not None:
            raise self._error
        if self._path is None:  # pragma: no cover - defensive
            raise RuntimeError(
                f"chromedriver prefetch for {self.major} produced no path"
            )
        return self._path


def ensure_chromedriver(major: str, *, timeout_s: float | None = None) -> str:
    """Return a cached chromedriver for ``major``, downloading it when absent."""
    with _PREFETCH_GUARD:
        job = _PREFETCH.get(major)
    if job is not None and job.running:
        return job.result(timeout=timeout_s)
    return _ensure_blocking(major, timeout_s=timeout_s)


def prefetch_chromedriver(
    major: str, *, timeout_s: float | None = None
) -> DriverPrefetch:
    """Start (or reuse) a background download of the chromedriver for ``major``."""
    with _PREFETCH_GUARD:
        job = _PREFETCH.get(major)
        if job is not None and (job.running or job._error is None):
            return job
        job = DriverPrefetch(major, timeout_s=timeout_s).start()
        _PREFETCH[major] = job
        return job


def prefetch_chromedriver_for_browser(
    *,
    debugger_address: str | None = None,
    binary: str | None = None,
    timeout_s: float | None = None,
) -> DriverPrefetch | None:
    """Detect the browser major and prefetch its driver; ``None`` if undetectable."""
    major = resolve_browser_major(debugger_address=debugger_address, binary=binary)
    if major is None:
        return None
    return prefetch_chromedriver(major, timeout_s=timeout_s)


def chromedriver_for_browser(
    *,
    debugger_address: str | None = None,
    binary: str | None = None,
    timeout_s: float | None = None,
) -> str:
    """Detect the browser major and return a matching driver, downloading if needed."""
    major = resolve_browser_major(debugger_address=debugger_address, binary=binary)
    if major is None:
        raise RuntimeError(
            "Could not determine the browser version; cannot match a chromedriver."
        )
    return ensure_chromedriver(major, timeout_s=timeout_s)
