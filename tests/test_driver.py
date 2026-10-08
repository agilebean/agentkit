"""Tests for agentkit.browser._driver (detection, cache, download, prefetch)."""
from __future__ import annotations

import io
import subprocess
import threading
import time
import urllib.request
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agentkit.browser import _driver
from agentkit.browser._driver import (
    DriverPrefetch,
    _cft_driver_url,
    _cft_platform_key,
    _chromedriver_download,
    _download_matching_driver,
    _http_download,
    _install_chromedriver,
    browser_major_from_binary,
    browser_major_from_cdp,
    chromedriver_major,
    ensure_chromedriver,
    find_cached_chromedriver,
    prefetch_chromedriver,
    prefetch_chromedriver_for_browser,
    resolve_browser_major,
)


class _FakeResponse:
    def __init__(self, payload: str) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return self._payload.encode()

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None


@pytest.fixture(autouse=True)
def _clear_prefetch_state() -> None:
    _driver._PREFETCH.clear()


class TestChromedriverMajor:
    def test_parses_chromedriver_version(self) -> None:
        proc = MagicMock(stdout="ChromeDriver 155.0.8059.39 (abc-refs/branch-heads)")
        with patch("agentkit.browser._driver.subprocess.run", return_value=proc):
            assert chromedriver_major("/cache/chromedriver") == "155"

    def test_returns_none_when_binary_unusable(self) -> None:
        with patch(
            "agentkit.browser._driver.subprocess.run",
            side_effect=OSError("not executable"),
        ):
            assert chromedriver_major("/cache/missing") is None


class TestBrowserMajorDetection:
    def test_cdp_parses_running_browser_major(self) -> None:
        with patch(
            "agentkit.browser._driver.urllib.request.urlopen",
            return_value=_FakeResponse('{"Browser": "Chrome/152.0.7977.76"}'),
        ):
            assert browser_major_from_cdp("127.0.0.1:9222") == "152"

    def test_cdp_returns_none_when_unreachable(self) -> None:
        with patch(
            "agentkit.browser._driver.urllib.request.urlopen",
            side_effect=OSError("refused"),
        ):
            assert browser_major_from_cdp("127.0.0.1:9222") is None

    def test_binary_parses_brave_version(self) -> None:
        proc = MagicMock(stdout="Brave Browser 155.1.97.56")
        with patch("agentkit.browser._driver.subprocess.run", return_value=proc):
            assert browser_major_from_binary("/path/brave") == "155"

    def test_resolve_prefers_running_browser(self) -> None:
        with (
            patch(
                "agentkit.browser._driver.browser_major_from_cdp", return_value="155"
            ),
            patch(
                "agentkit.browser._driver.browser_major_from_binary"
            ) as mock_binary,
        ):
            assert resolve_browser_major(debugger_address="127.0.0.1:9222") == "155"

        mock_binary.assert_not_called()

    def test_resolve_falls_back_to_binary(self) -> None:
        with (
            patch(
                "agentkit.browser._driver.browser_major_from_cdp", return_value=None
            ),
            patch(
                "agentkit.browser._driver.browser_major_from_binary",
                return_value="154",
            ),
        ):
            assert (
                resolve_browser_major(
                    debugger_address="127.0.0.1:9222", binary="/path/brave"
                )
                == "154"
            )


class TestFindCachedChromedriver:
    def _make(self, tmp_path: Path, version: str) -> Path:
        binary = tmp_path / "chromedriver" / "mac-arm64" / version / "chromedriver"
        binary.parent.mkdir(parents=True)
        binary.write_bytes(b"\x7fELF")
        return binary

    def test_finds_matching_major(self, tmp_path: Path) -> None:
        binary = self._make(tmp_path, "155.0.8059.39")
        with patch("agentkit.browser._driver.chromedriver_major", return_value="155"):
            found = find_cached_chromedriver("155", cache_root=tmp_path)
        assert found == str(binary)

    def test_ignores_other_major(self, tmp_path: Path) -> None:
        self._make(tmp_path, "154.0.8037.92")
        with patch("agentkit.browser._driver.chromedriver_major", return_value="154"):
            assert find_cached_chromedriver("155", cache_root=tmp_path) is None

    def test_ignores_version_dir_matching_but_unusable_binary(
        self, tmp_path: Path
    ) -> None:
        self._make(tmp_path, "155.0.8059.39")
        with patch("agentkit.browser._driver.chromedriver_major", return_value=None):
            assert find_cached_chromedriver("155", cache_root=tmp_path) is None


class TestEnsureChromedriver:
    def test_returns_cached_without_download(self, tmp_path: Path) -> None:
        with (
            patch(
                "agentkit.browser._driver.find_cached_chromedriver",
                return_value="/cache/chromedriver-155",
            ),
            patch(
                "agentkit.browser._driver._download_matching_driver"
            ) as mock_download,
        ):
            assert (
                ensure_chromedriver("155") == "/cache/chromedriver-155"
            )

        mock_download.assert_not_called()

    def test_downloads_under_lock_when_absent(self, tmp_path: Path) -> None:
        with (
            patch(
                "agentkit.browser._driver.find_cached_chromedriver",
                side_effect=[None, None],
            ),
            patch(
                "agentkit.browser._driver._selenium_cache_root",
                return_value=tmp_path,
            ),
            patch(
                "agentkit.browser._driver._download_matching_driver",
                return_value="/cache/chromedriver-155",
            ) as mock_download,
        ):
            assert ensure_chromedriver("155", timeout_s=42.0) == "/cache/chromedriver-155"

        mock_download.assert_called_once_with("155", 42.0)


class TestChromeForTestingLookup:
    def test_platform_key_on_apple_silicon(self) -> None:
        with (
            patch("agentkit.browser._driver.sys.platform", "darwin"),
            patch("agentkit.browser._driver.platform.machine", return_value="arm64"),
        ):
            assert _cft_platform_key() == "mac-arm64"

    def test_driver_url_selects_platform(self) -> None:
        entry = {
            "downloads": {
                "chromedriver": [
                    {"platform": "linux64", "url": "http://x/linux"},
                    {"platform": "mac-arm64", "url": "http://x/mac"},
                ]
            }
        }
        assert _cft_driver_url(entry, "mac-arm64") == "http://x/mac"
        assert _cft_driver_url(entry, "win64") is None

    def test_lookup_prefers_last_known_good(self) -> None:
        payload = {
            "channels": {
                "Stable": {
                    "version": "155.0.8059.39",
                    "downloads": {
                        "chromedriver": [
                            {"platform": "mac-arm64", "url": "http://x/mac155"}
                        ]
                    },
                }
            }
        }
        with patch("agentkit.browser._driver._fetch_json", return_value=payload):
            assert _chromedriver_download("155", 5.0) == (
                "155.0.8059.39",
                "http://x/mac155",
            )

    def test_lookup_returns_none_when_major_absent(self) -> None:
        with patch("agentkit.browser._driver._fetch_json", return_value={}):
            assert _chromedriver_download("999", 5.0) is None

    def test_download_raises_without_assets(self) -> None:
        with patch("agentkit.browser._driver._chromedriver_download", return_value=None):
            with pytest.raises(RuntimeError, match="major 999"):
                _download_matching_driver("999", 5.0)


class TestHttpDownload:
    def test_streams_to_file(self, tmp_path: Path) -> None:
        class _ChunkedResponse:
            def __init__(self) -> None:
                self._chunks = [b"ab", b"cd", b""]

            def read(self, size: int) -> bytes:
                return self._chunks.pop(0)

            def __enter__(self) -> "_ChunkedResponse":
                return self

            def __exit__(self, *args: object) -> None:
                return None

        dest = tmp_path / "payload"
        with patch(
            "agentkit.browser._driver.urllib.request.urlopen",
            return_value=_ChunkedResponse(),
        ):
            _http_download("http://x/file", dest, 30.0)

        assert dest.read_bytes() == b"abcd"

    def test_enforces_total_deadline(self, tmp_path: Path) -> None:
        class _NeverEndingResponse:
            def read(self, size: int) -> bytes:
                return b"x" * size

            def __enter__(self) -> "_NeverEndingResponse":
                return self

            def __exit__(self, *args: object) -> None:
                return None

        with patch(
            "agentkit.browser._driver.urllib.request.urlopen",
            return_value=_NeverEndingResponse(),
        ):
            with pytest.raises(TimeoutError, match="exceeded 0s"):
                _http_download("http://x/file", tmp_path / "payload", 0.0)


class TestInstallChromedriver:
    def test_extracts_binary_into_cache(self, tmp_path: Path) -> None:
        def fake_download(url: str, dest: Path, timeout_s: float) -> None:
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w") as archive:
                archive.writestr("chromedriver-mac-arm64/chromedriver", b"\x7fELF")
            Path(dest).write_bytes(buffer.getvalue())

        with (
            patch(
                "agentkit.browser._driver._http_download", side_effect=fake_download
            ) as mock_download,
            patch(
                "agentkit.browser._driver._selenium_cache_root",
                return_value=tmp_path,
            ),
            patch(
                "agentkit.browser._driver._cft_platform_key",
                return_value="mac-arm64",
            ),
            patch("agentkit.browser._driver.sys.platform", "darwin"),
            patch("agentkit.browser._driver.subprocess.run") as mock_xattr,
        ):
            path = _install_chromedriver("155.0.8059.39", "http://x/mac", 5.0)

        assert Path(path).read_bytes() == b"\x7fELF"
        assert path.endswith("chromedriver/mac-arm64/155.0.8059.39/chromedriver")
        mock_download.assert_called_once()
        mock_xattr.assert_called_once()
        download_dir = tmp_path / "chromedriver" / "mac-arm64" / "155.0.8059.39"
        assert list(download_dir.glob("*.download")) == []


class TestPrefetch:
    def test_prefetch_runs_in_background_and_reports_path(self) -> None:
        started = threading.Event()

        def slow_ensure(major: str, *, timeout_s: float | None = None) -> str:
            started.set()
            time.sleep(0.05)
            return f"/cache/chromedriver-{major}"

        with patch("agentkit.browser._driver._ensure_blocking", side_effect=slow_ensure):
            job = prefetch_chromedriver("155")

        assert isinstance(job, DriverPrefetch)
        assert job.running
        assert job.result(timeout=5) == "/cache/chromedriver-155"
        assert not job.running

    def test_prefetch_reuses_in_flight_job(self) -> None:
        blocker = threading.Event()

        def slow_ensure(major: str, *, timeout_s: float | None = None) -> str:
            blocker.wait(5)
            return f"/cache/chromedriver-{major}"

        with patch("agentkit.browser._driver._ensure_blocking", side_effect=slow_ensure):
            first = prefetch_chromedriver("155")
            second = prefetch_chromedriver("155")
            blocker.set()
            first.result(timeout=5)

        assert first is second

    def test_ensure_joins_running_prefetch(self) -> None:
        release = threading.Event()

        def slow_ensure(major: str, *, timeout_s: float | None = None) -> str:
            release.wait(5)
            return "/cache/chromedriver-155"

        with patch("agentkit.browser._driver._ensure_blocking", side_effect=slow_ensure):
            prefetch_chromedriver("155")
            release.set()
            assert ensure_chromedriver("155") == "/cache/chromedriver-155"

    def test_prefetch_for_browser_none_when_undetectable(self) -> None:
        with patch("agentkit.browser._driver.resolve_browser_major", return_value=None):
            assert prefetch_chromedriver_for_browser() is None

    def test_prefetch_for_browser_starts_job(self) -> None:
        with (
            patch(
                "agentkit.browser._driver.resolve_browser_major", return_value="155"
            ),
            patch(
                "agentkit.browser._driver.prefetch_chromedriver"
            ) as mock_prefetch,
        ):
            prefetch_chromedriver_for_browser(debugger_address="127.0.0.1:9222")

        mock_prefetch.assert_called_once()
        assert mock_prefetch.call_args.args[0] == "155"


class TestPrewarmCli:
    def test_returns_zero_and_prints_path(self, capsys: pytest.CaptureFixture) -> None:
        from agentkit.browser import prewarm

        with (
            patch(
                "agentkit.browser.prewarm.resolve_browser_major", return_value="155"
            ),
            patch(
                "agentkit.browser.prewarm.prefetch_chromedriver_for_browser"
            ) as mock_prefetch,
        ):
            mock_prefetch.return_value.result.return_value = "/cache/chromedriver-155"
            assert prewarm.main([]) == 0

        assert "/cache/chromedriver-155" in capsys.readouterr().out

    def test_returns_one_when_version_unknown(self, capsys: pytest.CaptureFixture) -> None:
        from agentkit.browser import prewarm

        with patch("agentkit.browser.prewarm.resolve_browser_major", return_value=None):
            assert prewarm.main([]) == 1
