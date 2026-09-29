"""Gmail SMTP send backend and credential resolution.

Send-only. Reading mail uses the Gmail API backend (:mod:`agentkit.gmail._client`).
The app password here is a Google account app password, a different credential
from the OAuth token: see the README and ``skills/gmail-setup/SKILL.md``.

The message shape, the sender-equals-login check, and the port fallback are
ported unchanged from invoice-admin's ``SmtpGmailBackend``; both projects now
import this one implementation.
"""
from __future__ import annotations

import mimetypes
import os
import smtplib
import ssl as _ssl
from email.message import EmailMessage
from pathlib import Path

from agentkit.gmail._client import GmailTransportError

# Project-specific names; kept working so existing shell setup and invoice-admin
# keep resolving the same secret.
ENV_SMTP_USER = "GOOGLEADS_GMAIL_SMTP_USER"
ENV_SMTP_PW = "GOOGLEADS_GMAIL_SMTP_APP_PASSWORD"
ENV_SMTP_PW_FILE = "GOOGLEADS_GMAIL_SMTP_APP_PASSWORD_FILE"

# Project-neutral aliases; used only when the GOOGLEADS_* name is unset.
ENV_SMTP_USER_ALIAS = "AGENTKIT_GMAIL_SMTP_USER"
ENV_SMTP_PW_ALIAS = "AGENTKIT_GMAIL_SMTP_APP_PASSWORD"
ENV_SMTP_PW_FILE_ALIAS = "AGENTKIT_GMAIL_SMTP_APP_PASSWORD_FILE"

DEFAULT_SMTP_USER = "chaehan.so@gmail.com"
DEFAULT_APP_PASSWORD_FILE = "~/.gmail/gmail-smtp-app-password"

_HOST = "smtp.gmail.com"
_PORT = 587


def _env(*names: str) -> str:
    for name in names:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return ""


def smtp_login_user() -> str:
    """SMTP login and From: address.

    ``GOOGLEADS_GMAIL_SMTP_USER`` (or the ``AGENTKIT_GMAIL_SMTP_USER`` alias)
    when set, otherwise :data:`DEFAULT_SMTP_USER`.
    """
    return _env(ENV_SMTP_USER, ENV_SMTP_USER_ALIAS) or DEFAULT_SMTP_USER


def _read_first_line(path: Path, label: str) -> str:
    if not path.is_file():
        raise ValueError(
            f"{label} is not a file: {path} (use chmod 600; never commit this file)."
        )
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    if not lines or not lines[0].strip():
        raise ValueError(f"{label} is empty: {path}")
    return lines[0].strip()


def smtp_app_password(*, default_file: Path | str | None = None) -> str:
    """Return the Gmail app password.

    Resolution order: the password-file env var, then the inline password env
    var, then *default_file* when the caller supplies one. A file wins over an
    inline value because the secret then stays out of the process environment.
    """
    raw_path = _env(ENV_SMTP_PW_FILE, ENV_SMTP_PW_FILE_ALIAS)
    if raw_path:
        return _read_first_line(Path(raw_path).expanduser(), ENV_SMTP_PW_FILE)
    inline = _env(ENV_SMTP_PW, ENV_SMTP_PW_ALIAS)
    if inline:
        return inline
    if default_file is not None:
        path = Path(default_file).expanduser()
        return _read_first_line(path, str(default_file))
    return ""


class SmtpGmailBackend:
    """Gmail **send-only** backend using SMTP and an **app password**.

    Create an app password: Google Account -> Security -> 2-Step Verification
    -> App passwords. Load it from ``GOOGLEADS_GMAIL_SMTP_APP_PASSWORD`` or the
    first line of ``GOOGLEADS_GMAIL_SMTP_APP_PASSWORD_FILE`` (never commit it).
    The From address must equal the SMTP login user.
    """

    def __init__(
        self,
        *,
        user: str,
        app_password: str,
        host: str = _HOST,
        port: int = _PORT,
    ) -> None:
        self._user = user.strip()
        self._app_password = app_password
        self._host = host
        self._port = port
        # Port 465 uses direct SSL; port 587 uses STARTTLS
        self._use_ssl = (port == 465)

    def list_messages(self, query: str, *, max_results: int = 10) -> list:
        raise GmailTransportError(
            "SmtpGmailBackend does not implement list_messages; use a Gmail API backend or Spark export."
        )

    def send_plain_text(
        self,
        *,
        sender: str,
        to: str,
        subject: str,
        body: str,
    ) -> str:
        self._check_sender(sender)
        msg = EmailMessage()
        msg["From"] = sender
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        self._send_message(msg)
        return "smtp:plain:ok"

    def send_text_with_pdf_attachment(
        self,
        *,
        sender: str,
        to: str,
        subject: str,
        body: str,
        pdf_path: Path,
        attachment_name: str,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
    ) -> str:
        self._check_sender(sender)
        path = pdf_path.expanduser()
        if not path.is_file():
            raise GmailTransportError(f"PDF attachment not a file: {path}")
        return self.send_text_with_attachment(
            sender=sender,
            to=to,
            subject=subject,
            body=body,
            attachment_path=path,
            attachment_name=attachment_name,
            attachment_mime="application/pdf",
            cc=cc,
            bcc=bcc,
            status="smtp:pdf:ok",
        )

    def send_text_with_attachment(
        self,
        *,
        sender: str,
        to: str,
        subject: str,
        body: str,
        attachment_path: Path,
        attachment_name: str | None = None,
        attachment_mime: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        status: str = "smtp:attachment:ok",
    ) -> str:
        """Send ``body`` with one arbitrary attachment; return an opaque handle."""
        self._check_sender(sender)
        path = Path(attachment_path).expanduser()
        if not path.is_file():
            raise GmailTransportError(f"Attachment not a file: {path}")
        msg = EmailMessage()
        msg["From"] = sender
        msg["To"] = to
        if cc:
            msg["Cc"] = ", ".join(cc)
        if bcc:
            msg["Bcc"] = ", ".join(bcc)
        msg["Subject"] = subject
        msg.set_content(body)
        mime = attachment_mime or (
            mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        )
        maintype, _, subtype = mime.partition("/")
        msg.add_attachment(
            path.read_bytes(),
            maintype=maintype or "application",
            subtype=subtype or "octet-stream",
            filename=attachment_name or path.name,
        )
        self._send_message(msg)
        return status

    def _check_sender(self, sender: str) -> None:
        if sender.strip() != self._user:
            raise GmailTransportError(
                f"SMTP login user {self._user!r} must match From address {sender!r} for Gmail."
            )

    def _send_message(self, msg: EmailMessage) -> None:
        last_error: Exception | None = None
        ports_to_try = [(self._host, self._port, self._use_ssl)]
        # Fallback: if 587 fails, try 465; if 465 fails, try 587
        if self._port == 587:
            ports_to_try.append((self._host, 465, True))
        elif self._port == 465:
            ports_to_try.append((self._host, 587, False))

        for host, port, use_ssl in ports_to_try:
            try:
                if use_ssl:
                    ctx = _ssl.create_default_context()
                    with smtplib.SMTP_SSL(host, port, timeout=120, context=ctx) as server:
                        server.login(self._user, self._app_password)
                        server.send_message(msg)
                else:
                    with smtplib.SMTP(host, port, timeout=120) as server:
                        server.starttls()
                        server.login(self._user, self._app_password)
                        server.send_message(msg)
                return
            except (smtplib.SMTPException, OSError) as e:
                last_error = e
                continue
        raise GmailTransportError(str(last_error or "SMTP connection failed"))
