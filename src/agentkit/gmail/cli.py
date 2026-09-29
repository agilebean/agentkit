"""CLI for Gmail read and send operations.

Read (Gmail API + OAuth token):

    python -m agentkit.gmail.cli search "from:test@example.com" --max 10
    python -m agentkit.gmail.cli fetch <message_id>
    python -m agentkit.gmail.cli attachments <message_id> --download ~/Downloads

Send (SMTP + app password):

    python -m agentkit.gmail.cli send --to you@example.com \\
        --subject "Hello" --body "Hi there"
    python -m agentkit.gmail.cli send --to you@example.com \\
        --subject "Invoice" --body-file body.txt --attachment invoice.pdf --dry-run

Credentials and failure modes: see README.md and skills/gmail-setup/SKILL.md.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from agentkit.gmail._smtp import DEFAULT_APP_PASSWORD_FILE


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agentkit.gmail.cli")
    sub = parser.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="Search Gmail messages.")
    s.add_argument("query", help="Gmail search query string.")
    s.add_argument("--max", type=int, default=10, help="Max results (default 10).")

    f = sub.add_parser("fetch", help="Fetch message body by ID.")
    f.add_argument("message_id", help="Gmail message ID.")

    a = sub.add_parser("attachments", help="Download attachments from a message.")
    a.add_argument("message_id", help="Gmail message ID.")
    a.add_argument("--download", default=".", help="Directory to save attachments (default: cwd).")

    snd = sub.add_parser("send", help="Send an email via Gmail SMTP (app password).")
    snd.add_argument("--to", required=True, help="Recipient address.")
    snd.add_argument("--subject", required=True, help="Subject line.")
    body = snd.add_mutually_exclusive_group(required=True)
    body.add_argument("--body", help="Message body text.")
    body.add_argument("--body-file", help="Read the message body from this file.")
    snd.add_argument("--attachment", help="Optional file to attach.")
    snd.add_argument("--cc", action="append", default=[], help="CC address (repeatable).")
    snd.add_argument("--bcc", action="append", default=[], help="BCC address (repeatable).")
    snd.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the message instead of sending; no SMTP connection.",
    )

    return parser


def _read_message_body(args: argparse.Namespace) -> str | None:
    if args.body is not None:
        return args.body
    path = Path(args.body_file).expanduser()
    if not path.is_file():
        print(f"Error: body file is not a file: {path}", file=sys.stderr)
        return None
    return path.read_text(encoding="utf-8")


def _cmd_send(args: argparse.Namespace, backend_override: object | None) -> int:
    from agentkit.gmail import (
        GmailTransportError,
        SmtpGmailBackend,
        smtp_app_password,
        smtp_login_user,
    )

    body = _read_message_body(args)
    if body is None:
        return 2

    sender = smtp_login_user()
    cc = list(args.cc) or None
    bcc = list(args.bcc) or None

    if args.dry_run:
        print(json.dumps({
            "dry_run": True,
            "from": sender,
            "to": args.to,
            "cc": args.cc,
            "bcc": args.bcc,
            "subject": args.subject,
            "attachment": str(args.attachment) if args.attachment else None,
            "body": body,
        }))
        return 0

    if backend_override is not None:
        backend = backend_override
    else:
        try:
            app_password = smtp_app_password(default_file=DEFAULT_APP_PASSWORD_FILE)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        if not app_password:
            print(
                "send: set Gmail SMTP app password env "
                "(GOOGLEADS_GMAIL_SMTP_APP_PASSWORD or "
                "GOOGLEADS_GMAIL_SMTP_APP_PASSWORD_FILE) or place it at "
                f"{DEFAULT_APP_PASSWORD_FILE}.",
                file=sys.stderr,
            )
            return 2
        backend = SmtpGmailBackend(user=sender, app_password=app_password)

    try:
        if args.attachment:
            status = backend.send_text_with_attachment(
                sender=sender,
                to=args.to,
                subject=args.subject,
                body=body,
                attachment_path=Path(args.attachment),
                cc=cc,
                bcc=bcc,
            )
        else:
            status = backend.send_plain_text(
                sender=sender,
                to=args.to,
                subject=args.subject,
                body=body,
            )
    except GmailTransportError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({"status": status}))
    return 0


def main(
    argv: list[str] | None = None,
    backend_override: object | None = None,
    send_backend_override: object | None = None,
) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    from agentkit.gmail import GmailAuthError

    if args.cmd == "send":
        return _cmd_send(args, send_backend_override)

    if backend_override is not None:
        backend = backend_override
    else:
        from agentkit.gmail import GmailApiBackend
        try:
            backend = GmailApiBackend()
        except GmailAuthError as exc:
            print(f"Auth error: {exc}", file=sys.stderr)
            return 2

    try:
        if args.cmd == "search":
            results = backend.search_messages(args.query, max_results=args.max)
            print(json.dumps(results))
            return 0

        if args.cmd == "fetch":
            body = backend.fetch_message_body(args.message_id)
            print(json.dumps({"id": args.message_id, "body": body}))
            return 0

        if args.cmd == "attachments":
            full = backend.fetch_message_full(args.message_id)
            attachments = full.get("attachments", [])
            download_dir = Path(args.download)
            download_dir.mkdir(parents=True, exist_ok=True)
            downloaded = []
            for att in attachments:
                data = backend.download_attachment(args.message_id, att["attachment_id"])
                filepath = download_dir / att["filename"]
                filepath.write_bytes(data)
                downloaded.append({
                    "filename": att["filename"],
                    "path": str(filepath),
                    "bytes": len(data),
                })
            print(json.dumps({"message_id": args.message_id, "downloaded": downloaded}))
            return 0

    except GmailAuthError as exc:
        print(f"Auth error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
