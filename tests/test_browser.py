"""Tests for agentkit.browser._browser (Brave/Chrome attach)."""
from __future__ import annotations

import urllib.request
from pathlib import Path
from unittest.mock import MagicMock, patch

from agentkit.browser import chrome_driver_attach
from agentkit.browser._browser import _cdp_browser_major, _ensure_cdp_page


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


class TestChromeDriverAttach:
    def test_uses_matching_driver_skipping_path(self) -> None:
        """Attach must resolve the driver via Selenium Manager with PATH drivers skipped."""
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
            patch("agentkit.browser._browser.SeleniumManager") as mock_mgr_cls,
            patch(
                "agentkit.browser._browser.webdriver.Chrome",
                return_value=fake_driver,
            ) as mock_chrome,
        ):
            mgr = mock_mgr_cls.return_value
            mgr.binary_paths.return_value = {
                "driver_path": "/cache/chromedriver-152",
            }

            result = chrome_driver_attach(
                debugger_address="127.0.0.1:9222",
                download_dir=Path("/tmp/dl"),
            )

        mgr.binary_paths.assert_called_once_with(
            [
                "--browser",
                "chrome",
                "--driver",
                "chromedriver",
                "--skip-driver-in-path",
                "--browser-version",
                "152",
            ]
        )
        service = mock_chrome.call_args.kwargs["service"]
        assert service.path == "/cache/chromedriver-152"
        assert result is fake_driver

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
            patch("agentkit.browser._browser.SeleniumManager") as mock_mgr_cls,
            patch(
                "agentkit.browser._browser.webdriver.Chrome",
                return_value=fake_driver,
            ),
        ):
            mgr = mock_mgr_cls.return_value
            mgr.binary_paths.return_value = {"driver_path": "/cache/cd"}

            chrome_driver_attach(debugger_address="127.0.0.1:9222")

        mgr.binary_paths.assert_called_once_with(
            [
                "--browser",
                "chrome",
                "--driver",
                "chromedriver",
                "--skip-driver-in-path",
                "--browser-path",
                brave,
            ]
        )


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
            patch("agentkit.browser._browser.SeleniumManager") as mock_mgr_cls,
            patch(
                "agentkit.browser._browser.webdriver.Chrome",
                return_value=fake_driver,
            ),
        ):
            mock_mgr_cls.return_value.binary_paths.return_value = {
                "driver_path": "/cache/chromedriver-152",
            }

            result = chrome_driver_attach(debugger_address="127.0.0.1:9222")

        assert result is fake_driver
        mock_ensure.assert_called_once_with("127.0.0.1:9222")
