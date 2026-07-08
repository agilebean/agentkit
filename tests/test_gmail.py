"""Tests for agentkit.gmail — mock googleapiclient, test payload decoding and body cleaning."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agentkit.gmail import (
    GmailApiBackend,
    GmailBackend,
    GmailFacade,
    GmailError,
    GmailAuthError,
    GmailMessageNotFoundError,
    clean_email_body,
    resolve_spec_to_message,
)
from agentkit.gmail._client import _extract_body_from_payload, _strip_html


class TestPayloadDecoding:
    def test_extract_plain_text(self):
        payload = {
            "mimeType": "text/plain",
            "body": {"data": "SGVsbG8gV29ybGQ="},  # "Hello World"
        }
        assert "Hello World" in _extract_body_from_payload(payload)

    def test_extract_html_converts_to_text(self):
        payload = {
            "mimeType": "text/html",
            "body": {"data": "PHA-SGk8L3A-"},
        }
        result = _extract_body_from_payload(payload)
        assert result is not None

    def test_extract_from_parts(self):
        payload = {
            "parts": [
                {"mimeType": "text/plain", "body": {"data": "SGVsbG8="}},
                {"mimeType": "text/html", "body": {"data": "PHAtQnllPC9wPg=="}},
            ]
        }
        result = _extract_body_from_payload(payload)
        assert "Hello" in result

    def test_extract_returns_empty_for_no_body(self):
        assert _extract_body_from_payload({}) == ""


class TestStripHtml:
    def test_removes_tags(self):
        assert "Hello World" in _strip_html("<html><body><p>Hello World</p></body></html>")

    def test_converts_br_to_newline(self):
        result = _strip_html("Line1<br>Line2")
        assert "Line1" in result
        assert "Line2" in result

    def test_removes_style_and_script(self):
        result = _strip_html("<style>body{}</style><script>x()</script>Clean")
        assert "Clean" in result
        assert "body{}" not in result


class TestCleanEmailBody:
    def test_removes_quoted_lines(self):
        body = "Hello\n> quoted text\n> more quoted\nWorld"
        cleaned = clean_email_body(body)
        assert "Hello" in cleaned
        assert "World" in cleaned
        assert "quoted text" not in cleaned

    def test_removes_german_sign_off(self):
        body = "Invoice attached\nMit freundlichen Gr\u00fc\u00dfen\nJohn Doe"
        cleaned = clean_email_body(body)
        assert "Invoice attached" in cleaned
        assert "Mit freundlichen" not in cleaned

    def test_removes_forwarded_blocks(self):
        body = "Here is the mail\n--- Forwarded message ---\nOriginal text"
        cleaned = clean_email_body(body)
        assert "Original text" not in cleaned

    def test_collapses_whitespace(self):
        body = "Line1\n\n\n\nLine2"
        cleaned = clean_email_body(body)
        assert cleaned.count("\n\n") == 1


class TestGmailFacade:
    def test_get_message_delegates_to_backend(self):
        backend = MagicMock(spec=GmailBackend)
        backend.fetch_message_body.return_value = "message body"
        facade = GmailFacade(backend)
        assert facade.get_message("msg1") == "message body"

    def test_get_message_wraps_error(self):
        backend = MagicMock(spec=GmailBackend)
        backend.fetch_message_body.side_effect = RuntimeError("boom")
        facade = GmailFacade(backend)
        with pytest.raises(GmailError, match="boom"):
            facade.get_message("msg1")

    def test_search_delegates(self):
        backend = MagicMock(spec=GmailBackend)
        backend.search_messages.return_value = [{"id": "1", "threadId": "t1"}]
        facade = GmailFacade(backend)
        assert facade.search("test") == [{"id": "1", "threadId": "t1"}]

    def test_get_attachment_delegates_to_backend(self):
        backend = MagicMock(spec=GmailBackend)
        backend.download_attachment.return_value = b"PDF_BYTES"
        facade = GmailFacade(backend)
        result = facade.get_attachment("msg1", "att1")
        assert result == b"PDF_BYTES"
        backend.download_attachment.assert_called_once_with("msg1", "att1")


class TestGmailApiBackend:
    def test_constructor_accepts_custom_path(self, tmp_path):
        token = tmp_path / "token.json"
        token.write_text('{"token": "test"}')
        with patch("google.oauth2.credentials.Credentials.from_authorized_user_file") as m:
            mock_creds = MagicMock()
            mock_creds.valid = True
            m.return_value = mock_creds
            backend = GmailApiBackend(credentials_path=token)
            assert backend._creds is not None

    def test_constructor_finds_token_at_google_oauth_path(self, tmp_path, monkeypatch):
        """Token at ~/.google/oauth_token.json is found without explicit path."""
        google_dir = tmp_path / ".google"
        google_dir.mkdir()
        token = google_dir / "oauth_token.json"
        token.write_text('{"token": "test"}')
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.delenv("GOOGLE_OAUTH_TOKEN", raising=False)
        with patch("google.oauth2.credentials.Credentials.from_authorized_user_file") as m:
            mock_creds = MagicMock()
            mock_creds.valid = True
            m.return_value = mock_creds
            backend = GmailApiBackend()
            assert backend._creds is not None
            assert str(token) in str(m.call_args[0][0])

    def test_explicit_path_takes_priority_over_google_oauth(self, tmp_path, monkeypatch):
        """Explicit credentials_path wins over ~/.google/oauth_token.json."""
        explicit = tmp_path / "explicit.json"
        explicit.write_text('{"token": "explicit"}')
        google_dir = tmp_path / ".google"
        google_dir.mkdir()
        (google_dir / "oauth_token.json").write_text('{"token": "default"}')
        monkeypatch.setenv("HOME", str(tmp_path))
        with patch("google.oauth2.credentials.Credentials.from_authorized_user_file") as m:
            mock_creds = MagicMock()
            mock_creds.valid = True
            m.return_value = mock_creds
            GmailApiBackend(credentials_path=explicit)
            assert str(explicit) in str(m.call_args[0][0])


class TestResolveSpecToMessage:
    def test_resolves_message_id_like_spec(self):
        backend = MagicMock(spec=GmailBackend)
        backend.fetch_message_body.return_value = "email body"
        msg_id, body = resolve_spec_to_message(backend, "msg@example.com")
        assert body == "email body"

    def test_falls_back_to_search(self):
        backend = MagicMock(spec=GmailBackend)
        backend.search_messages.return_value = [{"id": "abc", "threadId": "t1"}]
        backend.fetch_message_body.return_value = "found via search"
        msg_id, body = resolve_spec_to_message(backend, "some query")
        assert body == "found via search"

    def test_raises_when_no_results(self):
        backend = MagicMock(spec=GmailBackend)
        backend.fetch_message_body.side_effect = GmailMessageNotFoundError("abc")
        backend.search_messages.return_value = []
        with pytest.raises(GmailError, match="No messages found"):
            resolve_spec_to_message(backend, "nothing")


class TestExtractAttachments:
    def test_finds_attachment_in_flat_payload(self):
        from agentkit.gmail._client import _extract_attachments_from_payload
        payload = {
            "parts": [
                {"mimeType": "text/plain", "body": {"data": "SGVsbG8="}},
                {"mimeType": "application/pdf", "filename": "quote.pdf",
                 "body": {"attachmentId": "att123"}},
            ]
        }
        atts = _extract_attachments_from_payload(payload)
        assert len(atts) == 1
        assert atts[0]["filename"] == "quote.pdf"
        assert atts[0]["attachment_id"] == "att123"
        assert atts[0]["mime_type"] == "application/pdf"

    def test_finds_nested_attachments(self):
        from agentkit.gmail._client import _extract_attachments_from_payload
        payload = {
            "parts": [
                {"parts": [
                    {"mimeType": "text/plain", "body": {"data": "SGk="}},
                    {"mimeType": "image/png", "filename": "logo.png",
                     "body": {"attachmentId": "img1"}},
                ]},
                {"mimeType": "application/pdf", "filename": "doc.pdf",
                 "body": {"attachmentId": "att2"}},
            ]
        }
        atts = _extract_attachments_from_payload(payload)
        assert len(atts) == 2
        assert atts[0]["filename"] == "logo.png"
        assert atts[1]["filename"] == "doc.pdf"

    def test_no_attachments_returns_empty(self):
        from agentkit.gmail._client import _extract_attachments_from_payload
        payload = {"mimeType": "text/plain", "body": {"data": "SGVsbG8="}}
        assert _extract_attachments_from_payload(payload) == []

    def test_skips_inline_images_without_filename(self):
        from agentkit.gmail._client import _extract_attachments_from_payload
        payload = {
            "parts": [
                {"mimeType": "image/png", "filename": "",
                 "body": {"attachmentId": "inline1"}},
            ]
        }
        assert _extract_attachments_from_payload(payload) == []

    def test_skips_parts_without_attachment_id(self):
        from agentkit.gmail._client import _extract_attachments_from_payload
        payload = {
            "parts": [
                {"mimeType": "text/plain", "filename": "text.txt",
                 "body": {"data": "SGk="}},
            ]
        }
        assert _extract_attachments_from_payload(payload) == []


class TestFetchMessageFull:
    def test_returns_body_and_attachments(self):
        from unittest.mock import MagicMock
        backend = GmailApiBackend.__new__(GmailApiBackend)
        backend._service = MagicMock()
        mock_msg = {
            "payload": {
                "parts": [
                    {"mimeType": "text/plain", "body": {"data": "SGVsbG8="}},
                    {"mimeType": "application/pdf", "filename": "q.pdf",
                     "body": {"attachmentId": "a1"}},
                ]
            }
        }
        backend._service.users().messages().get().execute.return_value = mock_msg
        result = backend.fetch_message_full("msg1")
        assert "Hello" in result["body"]
        assert len(result["attachments"]) == 1
        assert result["attachments"][0]["filename"] == "q.pdf"

    def test_returns_empty_attachments_when_none(self):
        from unittest.mock import MagicMock
        backend = GmailApiBackend.__new__(GmailApiBackend)
        backend._service = MagicMock()
        mock_msg = {
            "payload": {
                "mimeType": "text/plain",
                "body": {"data": "SGVsbG8="},
            }
        }
        backend._service.users().messages().get().execute.return_value = mock_msg
        result = backend.fetch_message_full("msg1")
        assert result["attachments"] == []

    def test_raises_not_found_for_404(self):
        from unittest.mock import MagicMock
        from googleapiclient.errors import HttpError
        backend = GmailApiBackend.__new__(GmailApiBackend)
        backend._service = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status = 404
        backend._service.users().messages().get().execute.side_effect = HttpError(
            mock_resp, b'{"error": "not found"}'
        )
        with pytest.raises(GmailMessageNotFoundError):
            backend.fetch_message_full("badid")


class TestDownloadAttachment:
    def test_returns_decoded_bytes(self):
        import base64 as b64mod
        from unittest.mock import MagicMock
        backend = GmailApiBackend.__new__(GmailApiBackend)
        backend._service = MagicMock()
        encoded = b64mod.urlsafe_b64encode(b"PDF_CONTENT").decode().rstrip("=")
        backend._service.users().messages().attachments().get().execute.return_value = {
            "data": encoded
        }
        result = backend.download_attachment("msg1", "att1")
        assert result == b"PDF_CONTENT"

    def test_raises_gmail_error_on_http_error(self):
        from unittest.mock import MagicMock
        from googleapiclient.errors import HttpError
        backend = GmailApiBackend.__new__(GmailApiBackend)
        backend._service = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status = 500
        backend._service.users().messages().attachments().get().execute.side_effect = HttpError(
            mock_resp, b'{"error": "server error"}'
        )
        with pytest.raises(GmailError):
            backend.download_attachment("msg1", "att1")


class TestExceptions:
    def test_gmail_error_hierarchy(self):
        assert issubclass(GmailAuthError, GmailError)
        assert issubclass(GmailMessageNotFoundError, GmailError)

    def test_auth_error_message(self, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: Path("/nonexistent_home"))
        monkeypatch.delenv("GOOGLE_OAUTH_TOKEN", raising=False)
        with pytest.raises(GmailAuthError):
            GmailApiBackend(credentials_path=Path("/nonexistent.json"))
