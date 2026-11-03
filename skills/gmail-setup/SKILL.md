---
name: gmail-setup
description: Send and read Gmail through agentkit (SMTP app password for sending, OAuth token for reading), including the separate KUBS mailbox chaehanso@korea.ac.kr, which "check my kubs email" means. Use when wiring up, sending with, debugging, or re-consenting Gmail access, or to confirm credentials work before running an email pipeline.
---

# agentkit Gmail

Two credentials, two jobs:

| Credential | Job | Where it lives |
|------------|-----|----------------|
| OAuth token | Read via Gmail API (`search`, `fetch`, `attachments`) | `/Users/chaehan/.google/oauth_token.json` (default; override with `GOOGLE_OAUTH_TOKEN`) |
| OAuth token, Korea University | Read the KUBS mailbox `chaehanso@korea.ac.kr` | `/Users/chaehan/.google/oauth_token_korea.json` (pass as `GOOGLE_OAUTH_TOKEN`; never the default) |
| SMTP app password | Send via Gmail SMTP | `/Users/chaehan/.gmail/gmail-smtp-app-password` (first line) or `GOOGLEADS_GMAIL_SMTP_APP_PASSWORD` |

Project-neutral aliases for the SMTP names: `AGENTKIT_GMAIL_SMTP_USER`,
`AGENTKIT_GMAIL_SMTP_APP_PASSWORD`, `AGENTKIT_GMAIL_SMTP_APP_PASSWORD_FILE`. The
`GOOGLEADS_*` names win when both are set. Secrets stay in files, never in a
repo; `chmod 600` both.

## Send

```
python -m agentkit.gmail.cli send --to you@example.com \
    --subject "Hello" --body "Hi there"
python -m agentkit.gmail.cli send --to you@example.com --subject "Invoice" \
    --body-file body.txt --attachment invoice.pdf
python -m agentkit.gmail.cli send --to you@example.com --subject "Hello" \
    --body "Hi there" --dry-run
```

`--dry-run` prints the message as JSON and opens no connection. The From address
must equal the SMTP login user, or the send is refused.

## Read

1. Confirm the token exists at `~/.google/oauth_token.json` (or set `GOOGLE_OAUTH_TOKEN`).
2. `python -m agentkit.gmail.cli search "is:unread" --max 5`
3. One message: `python -m agentkit.gmail.cli fetch <message_id>`

## Which mailbox

Two addresses, one dot apart, so the request decides the token:

- `chaehan.so@gmail.com` is the primary. "check my email", "my inbox", or a
  request that names no address reads here, through the default token.
- `chaehanso@korea.ac.kr` is the KUBS mailbox. "check my kubs email", "the KUBS
  address", "korea.ac.kr" reads here, and the call carries
  `GOOGLE_OAUTH_TOKEN=/Users/chaehan/.google/oauth_token_korea.json`.

The default token is the primary, so an unnamed request needs no override. When
the named mailbox's token is dead, report `invalid_grant` for that address and
stop: never read the other mailbox in its place.

## Re-consent the OAuth token

Run when the read path reports `invalid_grant`.

```
pip install -e ".[gmail]"
python scripts/gmail_oauth_consent.py
```

Log in as `chaehan.so@gmail.com` and click Allow. The script writes
`~/.google/oauth_token.json` with the Gmail read, Gmail send, and Google Ads
scopes. A "Testing" OAuth client expires refresh tokens after 7 days; publish
the app to keep it alive.

For the KUBS mailbox:

```
python scripts/gmail_oauth_consent.py --login-hint chaehanso@korea.ac.kr \
    --token-out ~/.google/oauth_token_korea.json \
    --scope https://www.googleapis.com/auth/gmail.readonly \
    --scope https://www.googleapis.com/auth/gmail.send
```

The client is in Testing, so the address must also be on its test-user list,
otherwise the consent screen answers `403 access_denied`.

## The two failure modes

- `invalid_grant: Token has been expired or revoked.` Dead refresh token.
  Re-consent with `python scripts/gmail_oauth_consent.py`.
- `Connection refused` or a timeout. The host is blocked. Turn off the VPN or add
  a bypass; Surfshark must bypass `https://smtp.gmail.com` or sends fail.
