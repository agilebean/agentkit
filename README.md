# agentkit
Shared agents across projects by Chaehan So

## scripts

Standalone personal scripts. `~/.local/bin` holds symlinks to these files, so the repo is the source of truth.

- `switch-opencode-apikey` — rotate the opencode-go API key across every credential store. Writes `~/.local/share/opencode/auth.json` (opencode 1.x), `account.json`, and the `credential` table in `opencode.db` (opencode 2.x and OpenChamber), so the CLI and the app always agree.
  - `switch-opencode-apikey` — toggle to the other key
  - `switch-opencode-apikey --sync` — re-apply the current key to every store
  - `switch-opencode-apikey --list` — list all keys with labels
- `gmail_oauth_consent.py` — re-consent the shared Google OAuth token (`~/.google/oauth_token.json`). See Gmail below.

## Gmail

Read and send both run through agentkit. Read uses the Gmail API and an OAuth
token; send uses Gmail SMTP and an app password. They are two different
credentials and two different files.

```
python -m agentkit.gmail.cli search "from:test@example.com" --max 10
python -m agentkit.gmail.cli fetch <message_id>
python -m agentkit.gmail.cli attachments <message_id> --download ~/Downloads

python -m agentkit.gmail.cli send --to you@example.com \
    --subject "Hello" --body "Hi there"
python -m agentkit.gmail.cli send --to you@example.com \
    --subject "Invoice" --body-file body.txt --attachment invoice.pdf --dry-run
```

`send` flags: `--to`, `--subject`, `--body` or `--body-file`, `--attachment`,
`--cc`, `--bcc`, `--dry-run`. `--dry-run` prints the message as JSON and opens
no connection. The From address must equal the SMTP login user.

### Credentials

| Credential | Used for | Location | Env var |
|------------|----------|----------|---------|
| OAuth token (read) | Gmail API search/fetch/attachments | `/Users/chaehan/.google/oauth_token.json` | `GOOGLE_OAUTH_TOKEN` (optional; the path above is the default) |
| SMTP app password (send) | Gmail SMTP | file `/Users/chaehan/.gmail/gmail-smtp-app-password`, first line | `GOOGLEADS_GMAIL_SMTP_APP_PASSWORD_FILE` or inline `GOOGLEADS_GMAIL_SMTP_APP_PASSWORD` |

The same names work under the project-neutral aliases `AGENTKIT_GMAIL_SMTP_USER`,
`AGENTKIT_GMAIL_SMTP_APP_PASSWORD`, and `AGENTKIT_GMAIL_SMTP_APP_PASSWORD_FILE`.
The `GOOGLEADS_*` names win when both are set. SMTP login user:
`GOOGLEADS_GMAIL_SMTP_USER`, default `chaehan.so@gmail.com`.

Secrets stay in files, never in a repo. `chmod 600` both.

### Re-consent the OAuth token

```
pip install -e ".[gmail]"
python scripts/gmail_oauth_consent.py
```

It reads `~/.google/client_secret.json` (OAuth client, Desktop app type) and
writes `~/.google/oauth_token.json` with the Gmail read, Gmail send, and Google
Ads scopes. Log in as `chaehan.so@gmail.com` and click Allow. Both agentkit and
invoice-admin read the token from that one path.

If the OAuth client is in "Testing" publishing status, Google expires refresh
tokens after 7 days. Publish the app to keep the token alive.

### The two failure modes

- `invalid_grant: Token has been expired or revoked.` The refresh token is dead
  or revoked. Re-consent: `python scripts/gmail_oauth_consent.py`.
- `Connection refused`, `timed out`, or `[Errno 61] Connection refused` The SMTP
  or API host is blocked. Turn off the VPN or add a bypass. Surfshark must bypass
  `https://smtp.gmail.com`, or sends fail.

