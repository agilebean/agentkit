"""Browser helpers — Selenium/Brave attach and Chrome options for macOS automation."""
from __future__ import annotations

import json
import logging
import os
import platform
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.selenium_manager import SeleniumManager

logger = logging.getLogger(__name__)

_BRAVE_PATH_MACOS = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
_IS_MACOS = sys.platform == "darwin"

_CDP_BROWSER_VERSION_RE = re.compile(r"(?:Chrome|Chromium)/(\d+)")
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
# stalled download blocked the attach for minutes with no output (the reported
# "hang"). The metadata fetch is quick; the zip is a few megabytes and a slow link
# can legitimately need minutes, so its budget is generous but finite and progress
# is logged so the wait is never silent. Override with
# ``AGENTKIT_DRIVER_DOWNLOAD_TIMEOUT_S``.
_CFT_METADATA_TIMEOUT_S = 60.0
_CFT_DOWNLOAD_TIMEOUT_S = 600.0


def _brave_cdp_ready(address: str, timeout_s: float = 2.0) -> bool:
    try:
        req = urllib.request.Request(f"http://{address}/json/version")
        urllib.request.urlopen(req, timeout=timeout_s)
        return True
    except Exception:
        return False


def _cdp_browser_major(address: str, timeout_s: float = 2.0) -> str | None:
    """Major version of the browser currently listening on ``address``, or ``None``.

    Reads the CDP ``/json/version`` endpoint so the attach can pick a driver matching
    the **running** browser (Brave auto-updates; the on-disk binary may be newer).
    """
    try:
        req = urllib.request.Request(f"http://{address}/json/version")
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        match = _CDP_BROWSER_VERSION_RE.match(str(payload.get("Browser", "")))
        return match.group(1) if match else None
    except Exception:
        return None


def _cdp_targets(address: str, timeout_s: float = 2.0) -> list | None:
    """Target list from the CDP ``/json`` endpoint, or ``None`` when unreadable."""
    try:
        req = urllib.request.Request(f"http://{address}/json")
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        return payload if isinstance(payload, list) else None
    except Exception:
        return None


def _ensure_cdp_page(address: str, timeout_s: float = 2.0) -> None:
    """Guarantee at least one page target exists on the running browser.

    ChromeDriver's attach mode fails with "unable to discover open pages" when the
    browser has no page targets (a browser still running with every window closed).
    Creating an about:blank tab keeps the attach working. Best-effort: when the
    browser cannot be reached, return silently and let the attach surface its error.
    """
    targets = _cdp_targets(address, timeout_s=timeout_s)
    if targets is None:
        return
    if any(isinstance(t, dict) and t.get("type") == "page" for t in targets):
        return
    try:
        req = urllib.request.Request(
            f"http://{address}/json/new?about:blank", method="PUT"
        )
        with urllib.request.urlopen(req, timeout=timeout_s):
            pass
    except Exception:
        pass


def _brave_is_running() -> bool:
    """Check if process named 'Brave Browser' exists (with or without debug port)."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "Brave Browser"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except Exception:
        return False


def _kill_brave() -> None:
    subprocess.run(
        ["pkill", "-f", "Brave Browser"],
        capture_output=True,
    )


def ensure_brave_running(
    address: str = "127.0.0.1:9222",
    *,
    launch_timeout_s: float = 30.0,
) -> None:
    if _brave_cdp_ready(address):
        return

    binary = _BRAVE_PATH_MACOS
    if not Path(binary).exists():
        if not _IS_MACOS:
            return
        raise RuntimeError(
            f"Brave not found at {binary!r} and is not listening on {address}. "
            "Start Brave manually with --remote-debugging-port first."
        )

    # If Brave is already running without the debug port, kill it first
    # so the relaunch picks up the real profile with existing logins.
    if _brave_is_running():
        print(
            "Brave is running without --remote-debugging-port. "
            "Restarting with debug port...",
            file=sys.stderr,
        )
        _kill_brave()
        time.sleep(2)

    host, _, port_str = address.partition(":")
    port = int(port_str)

    args = [
        binary,
        f"--remote-debugging-port={port}",
        "--no-first-run",
    ]
    print(f"Launching Brave (port {port})...", file=sys.stderr)

    with open(os.devnull, "w") as devnull:
        subprocess.Popen(
            args,
            stdout=devnull,
            stderr=devnull,
            start_new_session=True,
        )

    print(f"Waiting for Brave, up to {launch_timeout_s:.0f}s...", file=sys.stderr)
    deadline = time.monotonic() + launch_timeout_s
    while time.monotonic() < deadline:
        if _brave_cdp_ready(address):
            print("Brave ready.", file=sys.stderr)
            return
        time.sleep(0.5)
    raise RuntimeError(
        f"Brave did not become ready on {address} within {launch_timeout_s:.0f}s."
    )


def build_chrome_options(
    *,
    download_dir: Path,
    user_data_dir: Path | None = None,
    binary_location: str | None = None,
    headless: bool = False,
) -> Options:
    opts = Options()
    dl = str(download_dir.resolve())
    prefs: dict[str, object] = {
        "download.default_directory": dl,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "plugins.always_open_pdf_externally": True,
    }
    opts.add_experimental_option("prefs", prefs)
    if user_data_dir is not None:
        opts.add_argument(f"--user-data-dir={user_data_dir.resolve()}")
    if binary_location:
        opts.binary_location = binary_location
    if headless:
        opts.add_argument("--headless=new")
    return opts


def build_chrome_options_for_remote_debugging(
    *,
    debugger_address: str,
    download_dir: Path | None = None,
) -> Options:
    opts = Options()
    opts.add_experimental_option("debuggerAddress", debugger_address.strip())
    if _IS_MACOS and Path(_BRAVE_PATH_MACOS).exists():
        opts.binary_location = _BRAVE_PATH_MACOS
    if download_dir is not None:
        dl = str(download_dir.resolve())
        prefs: dict[str, object] = {
            "download.default_directory": dl,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "plugins.always_open_pdf_externally": True,
        }
        opts.add_experimental_option("prefs", prefs)
    return opts


def _driver_major(path: str, timeout_s: float = 10.0) -> str | None:
    """Major version of the chromedriver at ``path``, or ``None`` when unusable.

    Selenium Manager's offline mode returns *some* cached driver even when it does
    not match the requested version, so the resolved binary must be checked before
    ChromeDriver is handed a browser it cannot drive.
    """
    try:
        proc = subprocess.run(
            [path, "--version"], capture_output=True, text=True, timeout=timeout_s
        )
    except Exception:
        return None
    match = _DRIVER_VERSION_RE.search(proc.stdout or "")
    return match.group(1) if match else None


def _selenium_manager_driver_path(args: list[str], *, timeout_s: float) -> str:
    """Resolve a driver path via Selenium Manager, capped at ``timeout_s``.

    Selenium's own wrapper runs the manager with :func:`subprocess.run` and no
    timeout, so a stalled network request keeps the caller blocked for the
    manager's full retry window. Invoking the binary ourselves lets us bound it.
    """
    binary = SeleniumManager._get_binary()
    cmd = [str(binary), *args, "--language-binding", "python", "--output", "json"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"Selenium Manager did not resolve a chromedriver within {timeout_s:.0f}s"
        ) from exc
    try:
        result = json.loads(proc.stdout)["result"]
    except Exception as exc:
        raise RuntimeError(
            proc.stderr.strip() or "Selenium Manager returned no usable output"
        ) from exc
    driver_path = result.get("driver_path")
    if proc.returncode != 0 or not driver_path:
        raise RuntimeError(
            result.get("message")
            or proc.stderr.strip()
            or "Selenium Manager found no chromedriver"
        )
    return driver_path


def _selenium_cache_root() -> Path:
    return Path(os.environ.get("SE_CACHE_PATH") or _SELENIUM_CACHE_DEFAULT)


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
                raise TimeoutError(
                    f"download from {url} exceeded {timeout_s:.0f}s"
                )
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
    binary_name = "chromedriver.exe" if sys.platform == "win32" else "chromedriver"
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


def chrome_driver_attach(
    *,
    debugger_address: str,
    download_dir: Path | None = None,
) -> webdriver.Chrome:
    opts = build_chrome_options_for_remote_debugging(
        debugger_address=debugger_address,
        download_dir=download_dir,
    )
    _ensure_cdp_page(debugger_address)
    # Resolve the chromedriver that matches the RUNNING browser instead of trusting
    # whatever chromedriver happens to be on PATH (brew-installed drivers lag Brave's
    # auto-updated Chromium and produce version-mismatch hangs).
    args = [
        "--browser",
        opts.capabilities["browserName"],
        "--driver",
        "chromedriver",
        "--skip-driver-in-path",
    ]
    major = _cdp_browser_major(debugger_address)
    binary = getattr(opts, "binary_location", None)
    if major:
        args += ["--browser-version", major]
    elif binary:
        args += ["--browser-path", str(binary)]

    def matching(path: str) -> bool:
        return major is None or _driver_major(path) == major

    # Offline first: Selenium Manager answers from its cache in about two seconds and
    # makes no network calls. It returns *some* cached driver regardless of the
    # requested version, so accept it only when its major matches the running browser.
    driver_path: str | None = None
    try:
        candidate = _selenium_manager_driver_path(args + ["--offline"], timeout_s=15.0)
        if matching(candidate):
            driver_path = candidate
    except RuntimeError:
        pass

    # Otherwise fetch the matching driver straight from Chrome for Testing. Selenium
    # Manager's online path is not used: its 300 s default network timeout (and its
    # fallback to a mismatched cached driver) is what produced the silent hang.
    if driver_path is None:
        if major is None:
            raise RuntimeError(
                "No cached chromedriver found and the running browser version is "
                "unknown; cannot pick a matching driver to download."
            )
        budget = _download_budget_s()
        logger.warning(
            "No cached chromedriver for browser %s; downloading from Chrome for "
            "Testing (up to %.0fs, once per browser upgrade)…",
            major,
            budget,
        )
        driver_path = _download_matching_driver(major, budget)
    service = ChromeService(executable_path=driver_path)
    return webdriver.Chrome(options=opts, service=service)
