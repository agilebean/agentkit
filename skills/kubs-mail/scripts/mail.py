#!/usr/bin/env python3
"""Read the KUBS mailbox (chaehanso@korea.ac.kr) — list, show, links.

Usage (run from the agentkit repo root, which puts src/ on the path):
    python ~/.agents/skills/kubs-mail/scripts/mail.py list "newer_than:14d -in:spam -in:trash" 60
    python ~/.agents/skills/kubs-mail/scripts/mail.py show <message_id>
    python ~/.agents/skills/kubs-mail/scripts/mail.py links <message_id>
"""
from __future__ import annotations

import base64
import os
import re
import sys

SRC = os.path.expanduser("~/Software/Prototypes/agentkit/src")
if os.path.isdir(SRC):
    sys.path.insert(0, SRC)

TOKEN = os.path.expanduser("~/.google/oauth_token_korea.json")
SCOPES = ("https://www.googleapis.com/auth/gmail.readonly",)

from agentkit.gmail._client import GmailApiBackend  # noqa: E402


def service():
    if not os.path.isfile(TOKEN):
        sys.exit(f"KUBS token missing at {TOKEN} — re-consent, do not fall back to the primary mailbox.")
    return GmailApiBackend(credentials_path=TOKEN, scopes=SCOPES)._get_service()


def _walk_html(payload, out):
    if payload.get("mimeType", "").startswith("text/html"):
        data = payload.get("body", {}).get("data")
        if data:
            out.append(base64.urlsafe_b64decode(data).decode("utf-8", "ignore"))
    for part in payload.get("parts") or []:
        _walk_html(part, out)


def cmd_list(argv):
    query = argv[0] if argv else "newer_than:14d -in:spam -in:trash"
    limit = int(argv[1]) if len(argv) > 1 else 40
    svc = service()
    ids = svc.users().messages().list(userId="me", q=query, maxResults=limit).execute().get("messages", [])
    for m in ids:
        d = svc.users().messages().get(
            userId="me", id=m["id"], format="metadata",
            metadataHeaders=["From", "To", "Subject", "Date"],
        ).execute()
        h = {x["name"]: x["value"] for x in d["payload"].get("headers", [])}
        print(f"{h.get('Date','')} | FROM {h.get('From','')} | {h.get('Subject','')} | "
              f"{','.join(d.get('labelIds', []))} | id={m['id']}")
        print(f"    {d.get('snippet','')[:200]}")


def cmd_show(argv):
    svc = service()
    f = svc.users().messages().get(userId="me", id=argv[0], format="full").execute()
    h = {x["name"]: x["value"] for x in f["payload"].get("headers", [])}
    body = ""
    html = []
    _walk_html(f["payload"], html)
    for chunk in html:
        text = re.sub(r"<br\s*/?>", "\n", chunk)
        text = re.sub(r"</(p|div|tr|h[1-6]|li)>", "\n", text)
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        if len(text) > len(body):
            body = text
    print(f"SUBJ: {h.get('Subject','')} | FROM: {h.get('From','')} | DATE: {h.get('Date','')}")
    print(body.strip()[:4000])


def cmd_links(argv):
    svc = service()
    f = svc.users().messages().get(userId="me", id=argv[0], format="full").execute()
    html = []
    _walk_html(f["payload"], html)
    seen = []
    for chunk in html:
        for href in re.findall(r'href="([^"]+)"', chunk):
            if href in seen:
                continue
            if href.startswith(("mailto:", "javascript:", "#")):
                continue
            if "reject_confirm" in href:  # the mailbox's own unsubscribe link
                continue
            if re.search(r"\.(png|jpg|jpeg|gif|svg)(\?|$)", href, re.I):
                continue
            seen.append(href)
    print("\n".join(seen[:20]) if seen else "(no html part — read the plain-text body with `show`)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    {"list": cmd_list, "show": cmd_show, "links": cmd_links}[sys.argv[1]](sys.argv[2:])
