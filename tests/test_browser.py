"""Tests for agentkit.browser._browser (Brave/Chrome attach)."""
from __future__ import annotations

import io
import urllib.request
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from agentkit.browser import chrome_driver_attach
from agentkit.browser._browser import (
    _cdp_browser_major,
    _cft_driver_url,
    _cft_platform_key,
    _chromedriver_download,
    _download_matching_driver,
    _driver_major,
    _ensure_cdp_page,
    _http_download,
    _install_chromedriver,
    _selenium_manager_driver_path,
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


class TestCdpBrowserMajor:
    def test_parses_running_browser_major(self) -> None:
        with patch(
            "agentkit.browser._browser.urllib.request.urlopen",
            return_value=_FakeResponse('{"Browser": "Chrome/152.0.7977.76"}'),
        ):
            assert _cdp_browser_major("127.0.0.1:9222") == "152"

    def test_returns_none_when_cdp_unreachable(self) -> None:
        with patch(
            "agentkit.browser._browser.urllib.request.urlopen",
            side_effect=OSError("refused"),
        ):
            assert _cdp_browser_major("127.0.0.1:9222") is None

    def test_returns_none_when_browser_field_missing(self) -> None:
        with patch(
            "agentkit.browser._browser.urllib.request.urlopen",
            return_value=_FakeResponse('{"webSocketDebuggerUrl": "ws://x"}'),
        ):
            assert _cdp_browser_major("127.0.0.1:9222") is None


class TestDriverMajor:
    def test_parses_chromedriver_version(self) -> None:
        proc = MagicMock(stdout="ChromeDriver 155.0.8059.39 (abc-refs/branch-heads)")
        with patch("agentkit.browser._browser.subprocess.run", return_value=proc):
            assert _driver_major("/cache/chromedriver") == "155"

    def test_returns_none_when_binary_unusable(self) -> None:
        with patch(
            "agentkit.browser._browser.subprocess.run",
            side_effect=OSError("not executable"),
        ):
            assert _driver_major("/cache/missing") is None


class TestSeleniumManagerDriverPath:
    def test_returns_driver_path_from_json(self) -> None:
        proc = MagicMock(
            returncode=0,
            stdout='{"result": {"driver_path": "/cache/cd"}}',
            stderr="",
        )
        with (
            patch(
                "agentkit.browser._browser.SeleniumManager._get_binary",
                return_value=Path("/sm"),
            ),
            patch(
                "agentkit.browser._browser.subprocess.run", return_value=proc
            ) as mock_run,
        ):
            path = _selenium_manager_driver_path(["--offline"], timeout_s=15.0)

        assert path == "/cache/cd"
        assert mock_run.call_args.kwargs["timeout"] == 15.0
        assert mock_run.call_args.args[0][0] == "/sm"

    def test_raises_on_timeout(self) -> None:
        import subprocess

        import pytest

        with (
            patch(
                "agentkit.browser._browser.SeleniumManager._get_binary",
                return_value=Path("/sm"),
            ),
            patch(
                "agentkit.browser._browser.subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd="sm", timeout=15),
            ),
        ):
            with pytest.raises(RuntimeError, match="within 15s"):
                _selenium_manager_driver_path(["--offline"], timeout_s=15.0)


class TestChromeForTestingDownload:
    def test_platform_key_on_apple_silicon(self) -> None:
        with (
            patch("agentkit.browser._browser.sys.platform", "darwin"),
            patch("agentkit.browser._browser.platform.machine", return_value="arm64"),
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

    def test_download_lookup_prefers_last_known_good(self) -> None:
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
        with patch(
            "agentkit.browser._browser._fetch_json", return_value=payload
        ):
            assert _chromedriver_download("155", 5.0) == (
                "155.0.8059.39",
                "http://x/mac155",
            )

    def test_download_lookup_returns_none_when_major_absent(self) -> None:
        with patch("agentkit.browser._browser._fetch_json", return_value={}):
            assert _chromedriver_download("999", 5.0) is None

    def test_download_matching_driver_raises_without_assets(self) -> None:
        import pytest

        with patch(
            "agentkit.browser._browser._chromedriver_download", return_value=None
        ):
            with pytest.raises(RuntimeError, match="major 999"):
                _download_matching_driver("999", 5.0)

    def test_http_download_streams_to_file(self, tmp_path: Path) -> None:
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
            "agentkit.browser._browser.urllib.request.urlopen",
            return_value=_ChunkedResponse(),
        ):
            _http_download("http://x/file", dest, 30.0)

        assert dest.read_bytes() == b"abcd"

    def test_http_download_enforces_total_deadline(self, tmp_path: Path) -> None:
        import pytest

        class _NeverEndingResponse:
            def read(self, size: int) -> bytes:
                return b"x" * size

            def __enter__(self) -> "_NeverEndingResponse":
                return self

            def __exit__(self, *args: object) -> None:
                return None

        with patch(
            "agentkit.browser._browser.urllib.request.urlopen",
            return_value=_NeverEndingResponse(),
        ):
            with pytest.raises(TimeoutError, match="exceeded 0s"):
                _http_download("http://x/file", tmp_path / "payload", 0.0)

    def test_install_chromedriver_extracts_binary(self, tmp_path: Path) -> None:
        def fake_download(url: str, dest: Path, timeout_s: float) -> None:
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w") as archive:
                archive.writestr("chromedriver-mac-arm64/chromedriver", b"\x7fELF")
            Path(dest).write_bytes(buffer.getvalue())

        with (
            patch(
                "agentkit.browser._browser._http_download", side_effect=fake_download
            ) as mock_download,
            patch(
                "agentkit.browser._browser._selenium_cache_root",
                return_value=tmp_path,
            ),
            patch(
                "agentkit.browser._browser._cft_platform_key",
                return_value="mac-arm64",
            ),
            patch("agentkit.browser._browser.sys.platform", "darwin"),
            patch("agentkit.browser._browser.subprocess.run") as mock_xattr,
        ):
            path = _install_chromedriver("155.0.8059.39", "http://x/mac", 5.0)

        assert Path(path).read_bytes() == b"\x7fELF"
        assert path.endswith("chromedriver/mac-arm64/155.0.8059.39/chromedriver")
        mock_download.assert_called_once()
        mock_xattr.assert_called_once()
        download_dir = tmp_path / "chromedriver" / "mac-arm64" / "155.0.8059.39"
        assert list(download_dir.glob("*.download")) == []


class TestChromeDriverAttach:
    def test_uses_cached_matching_driver_skipping_path(self) -> None:
        """Attach resolves the driver offline, with PATH drivers skipped."""
        fake_driver = MagicMock()
        opts = MagicMock()
        opts.capabilities = {"browserName": "chrome"}
        opts.binary_location = None

        with (
            patch(
                "agentkit.browser._browser.build_chrome_options_for_remote_debugging",
                return_value=opts,
            ),
            patch(
                "agentkit.browser._browser._cdp_browser_major",
                return_value="152",
            ),
            patch("agentkit.browser._browser._ensure_cdp_page"),
            patch(
                "agentkit.browser._browser._selenium_manager_driver_path",
                return_value="/cache/chromedriver-152",
            ) as mock_resolve,
            patch("agentkit.browser._browser._driver_major", return_value="152"),
            patch(
                "agentkit.browser._browser.webdriver.Chrome",
                return_value=fake_driver,
            ) as mock_chrome,
        ):
            result = chrome_driver_attach(
                debugger_address="127.0.0.1:9222",
                download_dir=Path("/tmp/dl"),
            )

        mock_resolve.assert_called_once()
        called_args = mock_resolve.call_args.args[0]
        assert called_args == [
            "--browser",
            "chrome",
            "--driver",
            "chromedriver",
            "--skip-driver-in-path",
            "--browser-version",
            "152",
            "--offline",
        ]
        service = mock_chrome.call_args.kwargs["service"]
        assert service.path == "/cache/chromedriver-152"
        assert result is fake_driver

    def test_downloads_when_cached_driver_major_differs(self) -> None:
        """A stale cached driver is rejected and a matching one downloaded."""
        fake_driver = MagicMock()
        opts = MagicMock()
        opts.capabilities = {"browserName": "chrome"}
        opts.binary_location = None

        with (
            patch(
                "agentkit.browser._browser.build_chrome_options_for_remote_debugging",
                return_value=opts,
            ),
            patch(
                "agentkit.browser._browser._cdp_browser_major", return_value="155"
            ),
            patch("agentkit.browser._browser._ensure_cdp_page"),
            patch(
                "agentkit.browser._browser._selenium_manager_driver_path",
                return_value="/cache/chromedriver-154",
            ),
            patch("agentkit.browser._browser._driver_major", return_value="154"),
            patch(
                "agentkit.browser._browser._download_matching_driver",
                return_value="/cache/chromedriver-155",
            ) as mock_download,
            patch(
                "agentkit.browser._browser.webdriver.Chrome",
                return_value=fake_driver,
            ) as mock_chrome,
        ):
            chrome_driver_attach(debugger_address="127.0.0.1:9222")

        assert mock_download.call_args.args[0] == "155"
        assert mock_download.call_args.args[1] > 0
        assert (
            mock_chrome.call_args.kwargs["service"].path == "/cache/chromedriver-155"
        )

    def test_raises_when_no_driver_can_be_downloaded(self) -> None:
        """A failed download surfaces an error instead of hanging."""
        import pytest

        opts = MagicMock()
        opts.capabilities = {"browserName": "chrome"}
        opts.binary_location = None

        with (
            patch(
                "agentkit.browser._browser.build_chrome_options_for_remote_debugging",
                return_value=opts,
            ),
            patch(
                "agentkit.browser._browser._cdp_browser_major", return_value="155"
            ),
            patch("agentkit.browser._browser._ensure_cdp_page"),
            patch(
                "agentkit.browser._browser._selenium_manager_driver_path",
                side_effect=RuntimeError("nothing cached"),
            ),
            patch(
                "agentkit.browser._browser._download_matching_driver",
                side_effect=RuntimeError("no chromedriver found"),
            ),
            patch("agentkit.browser._browser.webdriver.Chrome") as mock_chrome,
        ):
            with pytest.raises(RuntimeError, match="no chromedriver found"):
                chrome_driver_attach(debugger_address="127.0.0.1:9222")

        mock_chrome.assert_not_called()

    def test_falls_back_to_binary_path_when_cdp_unreachable(self) -> None:
        """Without a live CDP endpoint, the driver is resolved from the browser binary."""
        fake_driver = MagicMock()
        brave = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
        opts = MagicMock()
        opts.capabilities = {"browserName": "chrome"}
        opts.binary_location = brave

        with (
            patch(
                "agentkit.browser._browser.build_chrome_options_for_remote_debugging",
                return_value=opts,
            ),
            patch(
                "agentkit.browser._browser._cdp_browser_major",
                return_value=None,
            ),
            patch("agentkit.browser._browser._ensure_cdp_page"),
            patch(
                "agentkit.browser._browser._selenium_manager_driver_path",
                return_value="/cache/cd",
            ) as mock_resolve,
            patch(
                "agentkit.browser._browser.webdriver.Chrome",
                return_value=fake_driver,
            ),
        ):
            chrome_driver_attach(debugger_address="127.0.0.1:9222")

        assert mock_resolve.call_args.args[0] == [
            "--browser",
            "chrome",
            "--driver",
            "chromedriver",
            "--skip-driver-in-path",
            "--browser-path",
            brave,
            "--offline",
        ]

    def test_uses_downloaded_driver_when_cache_is_empty(self) -> None:
        """When nothing is cached, offline fails and the download is used."""
        fake_driver = MagicMock()
        opts = MagicMock()
        opts.capabilities = {"browserName": "chrome"}
        opts.binary_location = None

        with (
            patch(
                "agentkit.browser._browser.build_chrome_options_for_remote_debugging",
                return_value=opts,
            ),
            patch(
                "agentkit.browser._browser._cdp_browser_major", return_value="155"
            ),
            patch("agentkit.browser._browser._ensure_cdp_page"),
            patch(
                "agentkit.browser._browser._selenium_manager_driver_path",
                side_effect=RuntimeError("nothing cached"),
            ) as mock_resolve,
            patch(
                "agentkit.browser._browser._download_matching_driver",
                return_value="/cache/chromedriver-155",
            ) as mock_download,
            patch(
                "agentkit.browser._browser.webdriver.Chrome",
                return_value=fake_driver,
            ),
        ):
            chrome_driver_attach(debugger_address="127.0.0.1:9222")

        assert mock_resolve.call_args.args[0][-1] == "--offline"
        assert mock_download.call_args.args[0] == "155"
        assert mock_download.call_args.args[1] > 0


class TestEnsureCdpPage:
    """A page target must exist before ChromeDriver attaches (Brave with no windows)."""

    def test_opens_blank_tab_when_no_page_target(self) -> None:
        calls: list[urllib.request.Request] = []
        responses = iter(
            [
                _FakeResponse(
                    '[{"type": "service_worker", "url": "chrome-extension://x"}]'
                ),
                _FakeResponse('{"type": "page", "url": "about:blank"}'),
            ]
        )

        def fake_urlopen(req: urllib.request.Request, timeout: float | None = None):
            calls.append(req)
            return next(responses)

        with patch(
            "agentkit.browser._browser.urllib.request.urlopen",
            side_effect=fake_urlopen,
        ):
            _ensure_cdp_page("127.0.0.1:9222")

        assert [c.get_method() for c in calls] == ["GET", "PUT"]
        assert calls[0].full_url == "http://127.0.0.1:9222/json"
        assert calls[1].full_url == "http://127.0.0.1:9222/json/new?about:blank"

    def test_does_not_open_tab_when_page_exists(self) -> None:
        calls: list[urllib.request.Request] = []

        def fake_urlopen(req: urllib.request.Request, timeout: float | None = None):
            calls.append(req)
            return _FakeResponse('[{"type": "page", "url": "about:blank"}]')

        with patch(
            "agentkit.browser._browser.urllib.request.urlopen",
            side_effect=fake_urlopen,
        ):
            _ensure_cdp_page("127.0.0.1:9222")

        assert [c.get_method() for c in calls] == ["GET"]

    def test_silent_when_cdp_unreachable(self) -> None:
        with patch(
            "agentkit.browser._browser.urllib.request.urlopen",
            side_effect=OSError("connection refused"),
        ):
            _ensure_cdp_page("127.0.0.1:9222")

    def test_silent_when_new_tab_creation_fails(self) -> None:
        def fake_urlopen(req: urllib.request.Request, timeout: float | None = None):
            if req.full_url.endswith("/json"):
                return _FakeResponse("[]")
            raise OSError("boom")

        with patch(
            "agentkit.browser._browser.urllib.request.urlopen",
            side_effect=fake_urlopen,
        ):
            _ensure_cdp_page("127.0.0.1:9222")


class TestChromeDriverAttachEnsuresPage:
    def test_attach_ensures_page_exists_before_session(self) -> None:
        fake_driver = MagicMock()
        opts = MagicMock()
        opts.capabilities = {"browserName": "chrome"}
        opts.binary_location = None

        with (
            patch(
                "agentkit.browser._browser.build_chrome_options_for_remote_debugging",
                return_value=opts,
            ),
            patch(
                "agentkit.browser._browser._cdp_browser_major",
                return_value="152",
            ),
            patch("agentkit.browser._browser._ensure_cdp_page") as mock_ensure,
            patch(
                "agentkit.browser._browser._selenium_manager_driver_path",
                return_value="/cache/chromedriver-152",
            ),
            patch("agentkit.browser._browser._driver_major", return_value="152"),
            patch(
                "agentkit.browser._browser.webdriver.Chrome",
                return_value=fake_driver,
            ),
        ):
            result = chrome_driver_attach(debugger_address="127.0.0.1:9222")

        assert result is fake_driver
        mock_ensure.assert_called_once_with("127.0.0.1:9222")
