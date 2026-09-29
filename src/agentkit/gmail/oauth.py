"""Interactive Google OAuth consent, writing the shared token file.

The token grants the scopes the invoice (Gmail read + Google Ads) and commission
(Gmail read) flows use. It is written to ``~/.google/oauth_token.json`` by
default, the one location both agentkit and invoice-admin read.

This module needs ``google-auth-oauthlib`` (the ``gmail`` extra). Run it as::

    python scripts/gmail_oauth_consent.py

A revoked or expired refresh token makes the Gmail API answer
``invalid_grant: Token has been expired or revoked.`` Re-running this flow
re-consents and replaces the token file.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Gmail read for both flows; Google Ads for the invoice billing query.
DEFAULT_SCOPES = (
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/adwords",
)

DEFAULT_CLIENT_SECRET = "~/.google/client_secret.json"
DEFAULT_TOKEN_PATH = "~/.google/oauth_token.json"


def run_consent_flow(
    *,
    client_secret: Path | str = DEFAULT_CLIENT_SECRET,
    token_out: Path | str = DEFAULT_TOKEN_PATH,
    scopes: tuple[str, ...] = DEFAULT_SCOPES,
) -> Path:
    """Open the browser, run the consent flow, and write *token_out* (0600).

    Returns the token path. Raises if the client secret is missing or the
    ``google-auth-oauthlib`` extra is not installed.
    """
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:
        raise RuntimeError(
            "Missing google-auth-oauthlib. Install the agentkit gmail extra:\n"
            '  pip install -e ".[gmail]"'
        ) from exc

    secret_path = Path(client_secret).expanduser()
    if not secret_path.is_file():
        raise ValueError(f"OAuth client secret is not a file: {secret_path}")

    token_path = Path(token_out).expanduser()
    flow = InstalledAppFlow.from_client_secrets_file(str(secret_path), list(scopes))
    creds = flow.run_local_server(port=0)

    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(creds.to_json(), encoding="utf-8")
    token_path.chmod(0o600)
    return token_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="agentkit-gmail-oauth",
        description="Re-consent the shared Google OAuth token (Gmail + Ads scopes).",
    )
    parser.add_argument(
        "--client-secret",
        default=DEFAULT_CLIENT_SECRET,
        help=f"OAuth client JSON (default: {DEFAULT_CLIENT_SECRET}).",
    )
    parser.add_argument(
        "--token-out",
        default=DEFAULT_TOKEN_PATH,
        help=f"Token output path (default: {DEFAULT_TOKEN_PATH}).",
    )
    parser.add_argument(
        "--scope",
        action="append",
        dest="scopes",
        default=[],
        help="Extra or replacement scope (repeatable; defaults to the standard set).",
    )
    args = parser.parse_args(argv)
    scopes = tuple(args.scopes) if args.scopes else DEFAULT_SCOPES

    token_path = Path(args.token_out).expanduser()
    print("=" * 60)
    print("Google OAuth re-consent (Gmail + Google Ads)")
    print("=" * 60)
    print(f"Client secret: {Path(args.client_secret).expanduser()}")
    print(f"Token output:  {token_path}")
    for scope in scopes:
        print(f"  scope: {scope}")
    print()
    print("Opening the browser. Log in as chaehan.so@gmail.com and click Allow.")
    print()

    try:
        written = run_consent_flow(
            client_secret=args.client_secret,
            token_out=args.token_out,
            scopes=scopes,
        )
    except Exception as exc:
        print(f"OAuth consent failed: {exc}", file=sys.stderr)
        return 1

    print()
    print(f"Token saved: {written}")
    print("Export it in your shell profile if you want the API to find it by env:")
    print(f'  export GOOGLE_OAUTH_TOKEN="{written}"')
    print()
    print("Verify:")
    print('  python -m agentkit.gmail.cli search "is:unread" --max 1')
    print("  invoice save --dry-run")
    return 0


if __name__ == "__main__":
    sys.exit(main())
