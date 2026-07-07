---
name: sourcing
description: Search providers, request quotes, convert PDFs, and maintain minimal comparison tables. Use when the user asks to find vendors, compare services, get shipping/logistics/moving quotes, evaluate providers, or update a provider comparison table in memory/.
---

# Sourcing

## Onboarding

Before any work, use the question tool to collect:

1. **Working folder** — where to save PDFs and converted `.md` files (e.g., `~/Desktop/Shipping Quotes/`)
2. **Owner email** — for CC on all provider correspondence. Default: `chaehan.so@gmail.com`
3. **Language of correspondence** — Korean, English, or mixed (controls email tone and greeting style)
4. **Provider type** — what service is being sourced (e.g., 해외이사, freight forwarding, insurance). Determines search terms and directories.

Store answers in the memory file's header. Skip questions already answered there.

## Paths

Use `~` for all paths. Never hardcode `/Users/...`.

## Process

### 1. Search for providers (new sourcing tasks only)

If no Awaiting table exists yet, build one from scratch:
- Web search for the provider type in the relevant language (e.g., "해외이사 추천" for Korean international moving)
- Check certification bodies: BBB rating, IAM (International Association of Movers) membership, KOROMA (Korea International Movers Association)
- Cross-reference Naver blog reviews, Google reviews, and company websites
- For each candidate, record: company name, phone, website, quote page URL, reviews URL, email, status

Populate the Awaiting quotes table (structure below). Include the email for every provider — it is the user's primary search key to match a memory entry against their inbox. An entry without email is unlinkable.

### 2. Request quotes

Contact providers in the Awaiting table. If they reply with generic info only (no price), follow up with the item list link from the memory file.

### 3. Convert PDFs

Save attachments to the working folder. Run:
```
markitdown "file.pdf" -o "YYYY-MM-DD Company Quote $X.md"
```
Rename the PDF to match. Delete files the user instructs to delete.

### 4. Update the table

Read the `.md` files, extract volume/price/per CBM, and add rows to the comparison table. Ordering: waiting quotes at top, then descending Per CBM, rejected at the bottom.

## Table rules

### Comparison table

| Date | Provider - Email | Volume - Price | Per CBM | Evaluation |
|---|---|---|---|---|

- Merge Provider and Email with ` - `: `**Company Name** - email@example.com`
- Merge Volume and Price with ` - `: `80 CF (2.27 CBM) - **$2437**`
- Declare defaults once above the table (e.g., "Defaults: door-to-door, customs included, destination Seoul"). Do not add columns for declared defaults. Note deviations in Evaluation.
- Evaluation: factual, concise. Prefix with `REJECTED.` for rejected quotes. Multiple sentences allowed when the deviation needs explanation.

### Awaiting quotes table

| # | Company | Phone | 해외이사 Page | Quote Page | Reviews | Email | Status |

Include direct links to quote forms so the agent can act without further searching.

### Numbers and formatting

- CBM first, other units in parentheses: `4.59 CBM` not `163 CF`
- No thousand separators (commas) in any number — dollar amounts, CBM, weights. `$2676` not `$2,676`. Copy/paste into calculators must work without cleanup.
- Bold prices: `**$2676**`. No cents unless given.
- `YYYY-MM-DD` for all dates.

### Names

- Spell out company and person names in full: `Schumacher Cargo Logistics` not `Schumacher`.
- Common word abbreviations are fine: `Int'l` for `International`.
- Every provider row must include the exact email address — it is the search key for the user's inbox.

### Separators

- Use ` - ` as the default inline separator (Provider - Email, Volume - Price).
- Use ` / ` only for equal alternatives: `Adidas / Nike / Puma`.
- Never `<br>` — standard markdown tables do not support it.

## Email

### Gmail implementation

Sending and searching are implemented in the email-digest repo:
- **Send**: `~/Software/Prototypes/email-digest/src/unsubscribe/gmail_api_backend.py`, method `send_html_email` (lines 382-409). Uses `EmailMessage` + base64url + `users().messages().send()`.
- **Search/fetch**: `~/Software/Prototypes/agentkit/src/agentkit/gmail/_client.py`. `GmailApiBackend` with `fetch_message_body` and `search_messages`.

The existing `send_html_email` does not handle threading. For threaded replies, extend it:

```python
from email.message import EmailMessage
import base64
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

creds = Credentials.from_authorized_user_file('~/.google/oauth_token.json')
# Token must include gmail.send scope (not just gmail.readonly)
service = build('gmail', 'v1', credentials=creds)

msg = EmailMessage()
msg['Subject'] = 'Re: ' + original_subject  # preserve exact original subject
msg['From'] = from_addr
msg['To'] = recipient
msg['In-Reply-To'] = original_message_id   # fetch from the incoming message
msg['References'] = original_message_id
msg.set_content(body_text, subtype='plain', charset='utf-8')

raw = base64.urlsafe_b64encode(msg.as_bytes()).decode('ascii').rstrip('=')
service.users().messages().send(
    userId='me',
    body={'raw': raw, 'threadId': thread_id}  # thread_id from the original message
).execute()
```

### Threading

- Never change the subject. Reply with `Re: [exact original subject]`.
- Use `threadId` + `In-Reply-To` + `References` headers. Fetch all three from the original incoming message before sending.
- Before resending a corrected email, check per recipient: did a prior send already go to this address? If yes, verify whether the correction replaces the prior send or adds to it. Never resend the same content to a recipient who already received it unless explicitly instructed.

### CC rules

- Always CC the owner (email collected during onboarding) on all provider emails.
- CC any contacts listed in the memory file (e.g., cousin, agent).

### Tone — external recipients

These emails go to external providers, not to the user. The opposite of internal drafts applies:
- **Greeting**: always include. Korean: `안녕하세요` or appropriate honorific. English: `Dear [Name]`.
- **Closing**: always include. Korean: `감사합니다` or equivalent. English: `Best regards` or equivalent.
- **Body**: polite, professional. Korean uses formal endings (-습니다/합니다). English uses standard business correspondence.
- Match the language of correspondence collected during onboarding. If the provider is Korean, write in Korean. If English-speaking, write in English.

### Private position

Never embed the owner's negotiation floor, fallback strategy, minimum price, or internal reasoning in any outgoing message. These are confidential inputs for analysis, not material for the other party. Only include a specific number or phrase if the owner explicitly instructs for that specific message.

## Memory file

Each sourcing problem has its own `memory/` file. The file contains domain data only — no behavioral rules.

Contents:
- Onboarding answers (working folder, owner email, language, provider type)
- Awaiting quotes table with provider contact info
- Comparison table (quotes received)
- Key references: pickup/delivery addresses, item list URL, contacts
- A pointer to this skill (`> Formatting and email rules are in the sourcing skill`)

The memory file is the domain data. This skill is the behavior around it.
