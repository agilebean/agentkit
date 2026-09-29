#!/usr/bin/env python3
"""Re-consent the shared Google OAuth token (Gmail + Google Ads).

The exact procedure lives in agentkit: see README.md ("Gmail") and
src/agentkit/gmail/oauth.py. Install the gmail extra first:

    pip install -e ".[gmail]"

Then run:

    python scripts/gmail_oauth_consent.py

Writes ~/.google/oauth_token.json (0600). Use it when the Gmail API returns
"invalid_grant: Token has been expired or revoked."
"""
from agentkit.gmail.oauth import main

if __name__ == "__main__":
    raise SystemExit(main())
