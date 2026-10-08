"""Tests for agentkit.browser._browser (Brave/Chrome attach and CDP plumbing)."""
from __future__ import annotations

import urllib.request
from pathlib import Path
from unittest.mock import MagicMock, patch

from agentkit.browser import chrome_driver_attach
from agentkit.browser._browser import _ensure_cdp_page


class _FakeResponse:
    def __init__(self, payload: str) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return self._payload.encode()

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None


class TestChromeDriverAttach:
    def test_attaches_with_resolved_driver(self) -> None:
        """Attach uses the driver path resolved from the running browser."""
        fake_driver = MagicMock()
        opts = MagicMock()
        opts.binary_location = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"

        with (
            patch(
                "agentkit.browser._browser.build_chrome_options_for_remote_debugging",
                return_value=opts,
            ),
            patch(
                "agentkit.browser._browser.chromedriver_for_browser",
                return_value="/cache/chromedriver-155",
            ) as mock_resolve,
            patch("agentkit.browser._browser._ensure_cdp_page"),
            patch(
                "agentkit.browser._browser.webdriver.Chrome",
                return_value=fake_driver,
            ) as mock_chrome,
        ):
            result = chrome_driver_attach(
                debugger_address="127.0.0.1:9222",
                download_dir=Path("/tmp/dl"),
            )

        assert result is fake_driver
        assert mock_resolve.call_args.kwargs == {
            "debugger_address": "127.0.0.1:9222",
            "binary": opts.binary_location,
        }
        assert mock_chrome.call_args.kwargs["service"].path == "/cache/chromedriver-155"

    def test_propagates_resolution_error_without_session(self) -> None:
        """A failed driver resolution surfaces, and no browser session is opened."""
        import pytest

        opts = MagicMock()
        opts.binary_location = None

        with (
            patch(
                "agentkit.browser._browser.build_chrome_options_for_remote_debugging",
                return_value=opts,
            ),
            patch("agentkit.browser._browser._ensure_cdp_page"),
            patch(
                "agentkit.browser._browser.chromedriver_for_browser",
                side_effect=RuntimeError("no chromedriver"),
            ),
            patch("agentkit.browser._browser.webdriver.Chrome") as mock_chrome,
        ):
            with pytest.raises(RuntimeError, match="no chromedriver"):
                chrome_driver_attach(debugger_address="127.0.0.1:9222")

        mock_chrome.assert_not_called()


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


class TestAttachEnsuresPage:
    def test_attach_ensures_page_exists_before_session(self) -> None:
        fake_driver = MagicMock()
        opts = MagicMock()
        opts.binary_location = None

        with (
            patch(
                "agentkit.browser._browser.build_chrome_options_for_remote_debugging",
                return_value=opts,
            ),
            patch("agentkit.browser._browser._ensure_cdp_page") as mock_ensure,
            patch(
                "agentkit.browser._browser.chromedriver_for_browser",
                return_value="/cache/chromedriver-155",
            ),
            patch(
                "agentkit.browser._browser.webdriver.Chrome",
                return_value=fake_driver,
            ),
        ):
            result = chrome_driver_attach(debugger_address="127.0.0.1:9222")

        assert result is fake_driver
        mock_ensure.assert_called_once_with("127.0.0.1:9222")
