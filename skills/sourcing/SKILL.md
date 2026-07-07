---
name: sourcing
description: Sourcing workflow for any provider comparison problem. Use when the user says "do sourcing for [problem]", "update [problem]", "find vendors", "compare providers", "get quotes", or "check quotes for replies". Searches providers, requests quotes, converts PDFs, checks email for replies, and maintains comparison tables in memory/.
---

# Sourcing

## Triggers

- **New problem**: user says "do sourcing for [problem description]"
- **Existing problem**: user says "update [problem]" — problem name matches a file in `memory/`

## Onboarding (new problems only)

Use the question tool to collect:

1. **Working folder** — where to save PDFs and converted `.md` files
2. **Owner email** — for CC on all correspondence. Default: `chaehan.so@gmail.com`
3. **Language of correspondence** — controls email tone and search language
4. **Provider type** — what service is being sourced (determines search terms, directories, table metrics)
5. **Comparison metrics** — what columns to compare. Agent proposes based on provider type, user confirms. The last column should be a normalized comparison metric (e.g., Per CBM for shipping, $/month for subscriptions, $/unit for procurement).

Store all answers in the memory file header. Skip onboarding for existing problems — read from the file.

## Paths

Use `~` for all paths. Never hardcode `/Users/...`.

## Process — new problem

### 1. Search for providers

- Web search in the appropriate language for the provider type
- Find certification bodies, professional associations, and review directories relevant to the provider type and region. Use your own knowledge — do not assume a fixed list. Examples: BBB and IAM for US movers, KOROMA for Korean movers, but determine based on the specific problem.
- Cross-reference reviews across multiple sources
- For each candidate, record: company name, phone, website, quote page URL, reviews URL, email, status
- Populate the Awaiting quotes table. Every row MUST include email — it is the user's primary search key to match against their inbox. An entry without email is unlinkable.

### 2. Request quotes

Contact providers in the Awaiting table via email. If they reply with generic info only (no price), follow up with the item list or problem-specific details from the memory file.

### 3. Wait for replies

Quotes arrive as PDF attachments or email body text. When the user says "update [problem]", run the update workflow below.

## Process — update existing problem

### 1. Load the memory file

Match the problem name to a file in `memory/`. Read the onboarding answers, current tables, and key references.

### 2. Check Gmail for replies

Search for messages from each provider email in the Awaiting table, since the last table update. The last update date is the most recent date in the comparison table or the Status column.

### 3. Process each reply

- **Quote in PDF attachment**: save to working folder, run `markitdown "file.pdf" -o "YYYY-MM-DD Company Quote $X.md"`, rename PDF to match, extract metrics from the `.md` output
- **Quote in email body**: extract metrics directly from the email text
- **Generic info only (no price)**: note in Status column, follow up with item list link if appropriate
- **No reply**: leave Status unchanged

### 4. Update the comparison table

Add new rows. Sort: waiting quotes at top, then descending by normalized metric, rejected at bottom.

### 5. Report

What changed since last update: new quotes received, status changes, follow-ups needed.

## Table rules

### Comparison table

| Date | Provider - Email | [metric columns] | [normalized metric] | Evaluation |
|---|---|---|---|---|

- Metric columns are determined during onboarding
- Merge related metrics with ` - ` to reduce width: `Volume - Price`
- The last metric column is the normalized comparison metric (e.g., Per CBM, $/month, $/unit)
- Declare defaults once above the table (e.g., "Defaults: door-to-door, customs included, destination Seoul"). Do not add columns for declared defaults. Note deviations in Evaluation.
- Evaluation: factual, concise. Prefix with `REJECTED.` for rejected quotes. Multiple sentences allowed when the deviation needs explanation.

### Awaiting quotes table

| # | Company | Phone | Website | Quote Page | Reviews | Email | Status |

Column names adapt to the provider type (e.g., "해외이사 Page" for Korean movers, "Plans" for SaaS). Include direct links to quote forms. Every row MUST include email.

### Numbers and formatting

- Lead with the primary unit, secondary units in parentheses: `4.59 CBM` not `163 CF`
- No thousand separators (commas) in any number — dollar amounts, CBM, weights. `$2676` not `$2,676`. Copy/paste into calculators must work without cleanup.
- Bold prices: `**$2676**`. No cents unless given.
- `YYYY-MM-DD` for all dates.

### Names

- Spell out company and person names in full: `Schumacher Cargo Logistics` not `Schumacher`
- Common word abbreviations are fine: `Int'l` for `International`
- Every provider row must include the exact email address — it is the search key for the user's inbox

### Separators

- ` - ` is the default inline separator (Provider - Email, Volume - Price)
- ` / ` only for equal alternatives: `Adidas / Nike / Puma`
- Never `<br>` — standard markdown tables do not support it

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
- Before resending a corrected email, check per recipient: did a prior send already go to this address? If yes, verify whether the correction replaces or adds to it. Never resend the same content unless explicitly instructed.

### CC rules

- Always CC the owner (email from onboarding) on all provider emails.
- CC any contacts listed in the memory file.

### Tone — external recipients

These emails go to external providers. Greetings and closings ARE warranted:
- **Greeting**: always include. Korean: `안녕하세요` or appropriate honorific. English: `Dear [Name]`.
- **Closing**: always include. Korean: `감사합니다` or equivalent. English: `Best regards` or equivalent.
- **Body**: polite, professional. Korean uses formal endings (-습니다/합니다). English uses standard business correspondence.
- Match the language of correspondence from onboarding.

### Private position

Never embed the owner's negotiation floor, fallback strategy, minimum price, or internal reasoning in any outgoing message. These are confidential inputs for analysis, not material for the other party. Only include a specific number or phrase if the owner explicitly instructs for that specific message.

## Memory file

Each sourcing problem has its own `memory/` file. The file contains domain data only — no behavioral rules.

**Filename**: describe the problem, not the workflow. `shipping_ca2korea.md` not `sourcing_ca2korea.md`. No `sourcing/` folder. A problem may start as a question and become a sourcing problem later — the filename shouldn't force premature classification. The in-file pointer signals the workflow.

Contents:
- Onboarding answers (working folder, owner email, language, provider type, comparison metrics)
- Awaiting quotes table with provider contact info
- Comparison table (quotes received)
- Key references: addresses, item list URL, contacts
- Pointer to this skill: `> Formatting and email rules are in the sourcing skill`

The memory file is the domain data. This skill is the behavior around it.
