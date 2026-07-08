"""Tests for agentkit.gmail CLI — mock backend, test subcommands."""
from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from agentkit.gmail.cli import main


class TestSearchCLI:
    def test_search_prints_json_results(self, capsys):
        backend = MagicMock()
        backend.search_messages.return_value = [{"id": "abc", "threadId": "t1"}]
        rc = main(["search", "from:test@example.com"], backend_override=backend)
        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        assert out == [{"id": "abc", "threadId": "t1"}]

    def test_search_passes_max_results(self):
        backend = MagicMock()
        backend.search_messages.return_value = []
        main(["search", "test", "--max", "5"], backend_override=backend)
        backend.search_messages.assert_called_once_with("test", max_results=5)

    def test_search_default_max_is_10(self):
        backend = MagicMock()
        backend.search_messages.return_value = []
        main(["search", "test"], backend_override=backend)
        backend.search_messages.assert_called_once_with("test", max_results=10)

    def test_search_error_returns_1(self, capsys):
        backend = MagicMock()
        backend.search_messages.side_effect = RuntimeError("auth failed")
        rc = main(["search", "test"], backend_override=backend)
        assert rc == 1
        assert "auth failed" in capsys.readouterr().err


class TestFetchCLI:
    def test_fetch_prints_body_json(self, capsys):
        backend = MagicMock()
        backend.fetch_message_body.return_value = "email body text"
        rc = main(["fetch", "msg123"], backend_override=backend)
        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        assert out == {"id": "msg123", "body": "email body text"}

    def test_fetch_error_returns_1(self, capsys):
        backend = MagicMock()
        backend.fetch_message_body.side_effect = RuntimeError("not found")
        rc = main(["fetch", "badid"], backend_override=backend)
        assert rc == 1


class TestAttachmentsCLI:
    def test_attachments_downloads_to_dir(self, tmp_path):
        backend = MagicMock()
        backend.fetch_message_full.return_value = {
            "body": "text",
            "attachments": [
                {"filename": "quote.pdf", "attachment_id": "att1",
                 "mime_type": "application/pdf"},
            ],
        }
        backend.download_attachment.return_value = b"PDF_BYTES"
        rc = main(["attachments", "msg123", "--download", str(tmp_path)],
                   backend_override=backend)
        assert rc == 0
        saved = (tmp_path / "quote.pdf").read_bytes()
        assert saved == b"PDF_BYTES"

    def test_attachments_no_attachments_prints_empty(self, tmp_path, capsys):
        backend = MagicMock()
        backend.fetch_message_full.return_value = {
            "body": "text",
            "attachments": [],
        }
        rc = main(["attachments", "msg123", "--download", str(tmp_path)],
                   backend_override=backend)
        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        assert out["downloaded"] == []

    def test_attachments_creates_dir_if_missing(self, tmp_path):
        backend = MagicMock()
        backend.fetch_message_full.return_value = {
            "body": "text",
            "attachments": [
                {"filename": "f.pdf", "attachment_id": "a1", "mime_type": "application/pdf"},
            ],
        }
        backend.download_attachment.return_value = b"data"
        target = tmp_path / "newdir"
        rc = main(["attachments", "msg1", "--download", str(target)],
                   backend_override=backend)
        assert rc == 0
        assert (target / "f.pdf").exists()


class TestNoCredentials:
    def test_search_without_credentials_returns_2(self, capsys, monkeypatch):
        """CLI returns exit code 2 and auth message when no Gmail credentials found."""
        from unittest.mock import patch
        from agentkit.gmail import GmailAuthError
        with patch("agentkit.gmail.GmailApiBackend", side_effect=GmailAuthError("No valid Gmail credentials found")):
            rc = main(["search", "test"])
        assert rc == 2
        err = capsys.readouterr().err
        assert "auth" in err.lower() or "credentials" in err.lower()

    def test_fetch_without_credentials_returns_2(self, capsys):
        """CLI returns exit code 2 for fetch when no credentials found."""
        from unittest.mock import patch
        from agentkit.gmail import GmailAuthError
        with patch("agentkit.gmail.GmailApiBackend", side_effect=GmailAuthError("No valid Gmail credentials found")):
            rc = main(["fetch", "msg123"])
        assert rc == 2
