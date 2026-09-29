"""Tests for agentkit.gmail SMTP send backend and credential resolution.

No network: ``smtplib.SMTP`` is replaced with a fake.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agentkit.gmail import (
    GmailTransportError,
    SmtpGmailBackend,
    smtp_app_password,
    smtp_login_user,
)
from agentkit.gmail import _smtp


@patch("agentkit.gmail._smtp.smtplib.SMTP")
def test_smtp_send_text_with_pdf_attachment(
    mock_smtp_class: MagicMock,
    tmp_path: Path,
) -> None:
    pdf = tmp_path / "inv.pdf"
    pdf.write_bytes(b"%PDF-1.4 test bytes")

    mock_server = MagicMock()
    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_server)
    mock_ctx.__exit__ = MagicMock(return_value=False)
    mock_smtp_class.return_value = mock_ctx

    backend = SmtpGmailBackend(user="me@gmail.com", app_password="app-secret")
    result = backend.send_text_with_pdf_attachment(
        sender="me@gmail.com",
        to="jack@example.com",
        subject="Invoice test",
        body="Please see attached.\n",
        pdf_path=pdf,
        attachment_name="google-ads-invoice_test.pdf",
    )

    assert result == "smtp:pdf:ok"
    mock_smtp_class.assert_called_once()
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with("me@gmail.com", "app-secret")
    mock_server.send_message.assert_called_once()
    sent = mock_server.send_message.call_args[0][0]
    assert sent["Subject"] == "Invoice test"
    assert sent["To"] == "jack@example.com"


def test_smtp_rejects_sender_mismatch(tmp_path: Path) -> None:
    pdf = tmp_path / "a.pdf"
    pdf.write_bytes(b"%PDF")
    backend = SmtpGmailBackend(user="real@gmail.com", app_password="x")
    with pytest.raises(GmailTransportError, match="must match From"):
        backend.send_text_with_pdf_attachment(
            sender="other@gmail.com",
            to="a@b.com",
            subject="s",
            body="b",
            pdf_path=pdf,
            attachment_name="a.pdf",
        )


def test_smtp_list_messages_raises() -> None:
    backend = SmtpGmailBackend(user="u@gmail.com", app_password="x")
    with pytest.raises(GmailTransportError, match="does not implement list_messages"):
        backend.list_messages("q")


@patch("agentkit.gmail._smtp.smtplib.SMTP")
def test_smtp_send_plain_text_sets_headers(mock_smtp_class: MagicMock) -> None:
    mock_server = MagicMock()
    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_server)
    mock_ctx.__exit__ = MagicMock(return_value=False)
    mock_smtp_class.return_value = mock_ctx

    backend = SmtpGmailBackend(user="me@gmail.com", app_password="app-secret")
    result = backend.send_plain_text(
        sender="me@gmail.com",
        to="you@example.com",
        subject="Hi",
        body="Hello\n",
    )
    assert result == "smtp:plain:ok"
    sent = mock_server.send_message.call_args[0][0]
    assert sent["From"] == "me@gmail.com"
    assert sent["Subject"] == "Hi"


class TestCredentialResolution:
    def test_login_user_defaults_to_gmail_account(self, monkeypatch) -> None:
        monkeypatch.delenv("GOOGLEADS_GMAIL_SMTP_USER", raising=False)
        monkeypatch.delenv("AGENTKIT_GMAIL_SMTP_USER", raising=False)
        assert smtp_login_user() == "chaehan.so@gmail.com"

    def test_login_user_prefers_googleads_name(self, monkeypatch) -> None:
        monkeypatch.setenv("GOOGLEADS_GMAIL_SMTP_USER", "a@gmail.com")
        monkeypatch.setenv("AGENTKIT_GMAIL_SMTP_USER", "b@gmail.com")
        assert smtp_login_user() == "a@gmail.com"

    def test_login_user_uses_neutral_alias(self, monkeypatch) -> None:
        monkeypatch.delenv("GOOGLEADS_GMAIL_SMTP_USER", raising=False)
        monkeypatch.setenv("AGENTKIT_GMAIL_SMTP_USER", "b@gmail.com")
        assert smtp_login_user() == "b@gmail.com"

    def test_password_file_wins_over_inline(self, monkeypatch, tmp_path: Path) -> None:
        pw_file = tmp_path / "pw"
        pw_file.write_text("file-secret\n")
        monkeypatch.setenv("GOOGLEADS_GMAIL_SMTP_APP_PASSWORD_FILE", str(pw_file))
        monkeypatch.setenv("GOOGLEADS_GMAIL_SMTP_APP_PASSWORD", "inline-secret")
        assert smtp_app_password() == "file-secret"

    def test_inline_password_used_when_no_file(self, monkeypatch) -> None:
        monkeypatch.delenv("GOOGLEADS_GMAIL_SMTP_APP_PASSWORD_FILE", raising=False)
        monkeypatch.delenv("AGENTKIT_GMAIL_SMTP_APP_PASSWORD_FILE", raising=False)
        monkeypatch.setenv("GOOGLEADS_GMAIL_SMTP_APP_PASSWORD", "inline-secret")
        assert smtp_app_password() == "inline-secret"

    def test_default_file_used_as_last_resort(self, monkeypatch, tmp_path: Path) -> None:
        monkeypatch.delenv("GOOGLEADS_GMAIL_SMTP_APP_PASSWORD_FILE", raising=False)
        monkeypatch.delenv("AGENTKIT_GMAIL_SMTP_APP_PASSWORD_FILE", raising=False)
        monkeypatch.delenv("GOOGLEADS_GMAIL_SMTP_APP_PASSWORD", raising=False)
        monkeypatch.delenv("AGENTKIT_GMAIL_SMTP_APP_PASSWORD", raising=False)
        default = tmp_path / "default-pw"
        default.write_text("default-secret\n")
        assert smtp_app_password(default_file=default) == "default-secret"

    def test_missing_default_file_raises(self, monkeypatch, tmp_path: Path) -> None:
        monkeypatch.delenv("GOOGLEADS_GMAIL_SMTP_APP_PASSWORD_FILE", raising=False)
        monkeypatch.delenv("AGENTKIT_GMAIL_SMTP_APP_PASSWORD_FILE", raising=False)
        monkeypatch.delenv("GOOGLEADS_GMAIL_SMTP_APP_PASSWORD", raising=False)
        monkeypatch.delenv("AGENTKIT_GMAIL_SMTP_APP_PASSWORD", raising=False)
        with pytest.raises(ValueError, match="not a file"):
            smtp_app_password(default_file=tmp_path / "missing")

    def test_empty_env_returns_empty_string(self, monkeypatch) -> None:
        for name in (
            _smtp.ENV_SMTP_PW_FILE,
            _smtp.ENV_SMTP_PW_FILE_ALIAS,
            _smtp.ENV_SMTP_PW,
            _smtp.ENV_SMTP_PW_ALIAS,
        ):
            monkeypatch.delenv(name, raising=False)
        assert smtp_app_password() == ""
