"""CLI for Gmail search and attachment operations.

Usage:
    python -m agentkit.gmail.cli search "from:test@example.com" --max 10
    python -m agentkit.gmail.cli fetch <message_id>
    python -m agentkit.gmail.cli attachments <message_id> --download ~/Downloads
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


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

    return parser


def main(
    argv: list[str] | None = None,
    backend_override: object | None = None,
) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    from agentkit.gmail import GmailAuthError

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
