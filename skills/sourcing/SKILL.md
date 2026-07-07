---
name: sourcing
description: Search providers, request quotes, convert PDFs, and maintain minimal comparison tables. Use when the user asks to find vendors, compare services, get shipping/logistics/moving quotes, evaluate providers, or update a provider comparison table in memory/.
---

# Sourcing

## Process

1. **Request quotes** from providers in the Awaiting table. If they reply with generic info only (no price), follow up with the item list link from the memory file.
2. **Convert PDFs.** Save attachments. Run `markitdown "file.pdf" -o "YYYY-MM-DD Company Quote $X.md"`. Rename the PDF to match. Delete files the user instructs to delete. Use `~` paths — never hardcode `/Users/...`.
3. **Update the table.** Read the `.md` files, extract volume/price/per CBM, and add rows ordered by descending Per CBM (waiting first, rejected last).

## Table rules

Every comparison table follows this structure. Delete columns covered by defaults.

| Date | Provider - Email | Volume / Price | Per CBM | Evaluation |
|---|---|---|---|---|

**Structure**
- Merge Provider and Email: `**Company Name** - email@example.com`
- Merge Volume and Price: `80 CF (2.27 CBM) / **$2437**`
- Declare defaults once above the table. Only note deviations in Evaluation.

**Numbers and formatting**
- CBM first, other units in parentheses: `4.59 CBM` not `163 CF`
- No thousand separators (commas): `$2676` not `$2676`. Copy/paste into calculators must work without cleanup.
- Bold prices: `**$2676**`. No cents unless given.
- YYYY-MM-DD for all dates.
- No abbreviations. `International Sea and Air Shipping` not `International Sea & Air`.
- Use ` / ` as the inline separator. Never `<br>` — standard markdown tables do not support it.
- Evaluation column: factual, one sentence. Deviations from defaults go here.

**Ordering**: waiting quotes at top, then descending Per CBM, rejected at the bottom.

## Awaiting quotes table

Before receiving a quote, providers live in a separate table with these columns:

| # | Company | Phone | 해외이사 Page | Quote Page | Reviews | Email | Status |

Include direct links to quote forms so the agent can act without further searching.

## Email

**Sending**
- Gmail API via `~/.google/oauth_token.json`. Pattern from email-digest:
  ```python
  creds = Credentials.from_authorized_user_file('~/.google/oauth_token.json')
  gmail = build('gmail', 'v1', credentials=creds)
  # Send with threadId for proper conversation threading
  gmail.users().messages().send(userId='me', body={'raw': raw, 'threadId': thread_id})
  ```

**Threading**
- Never change the subject — reply with `Re: [original subject]`.
- Use `threadId` + `In-Reply-To` + `References` headers. Fetch the correct threadId from the original incoming message before sending.
- Check per recipient: "Did any prior iteration already deliver to this address?" Skip duplicates.

**CC rules**
- Always CC the owner (`chaehan.so@gmail.com`) on all provider emails.
- CC any contacts listed in the memory file (e.g., cousin, agent).

## When disputed

If the user says your account of events is wrong, query the ground truth:
- Re-list message IDs from Gmail
- Re-read files from disk
- Re-run searches

Do not reason from memory. Present the raw data, then compare.

## Memory file

Each sourcing problem has its own `memory/` file. The file should contain:
- Awaiting quotes table with provider contact info
- Comparison table (quotes received)
- Process section above the first table — the three steps repeated here, plus domain-specific addresses, contacts, and item list URLs
- A pointer to this skill (`> Formatting and email rules are in the sourcing skill`)

The memory file is the domain data. This skill is the behavior around it.
