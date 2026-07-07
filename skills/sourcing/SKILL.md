---
name: sourcing
description: Search providers, request quotes, convert PDFs, and maintain minimal comparison tables. Use when the user asks to find vendors, compare services, get shipping/logistics/moving quotes, evaluate providers, or update a provider comparison table in memory/.
---

# Sourcing

## Process

1. **Request quotes** from providers in the Awaiting table. If they reply with generic info only (no price), follow up with the item list link from the memory file.
2. **Convert PDFs.** Save attachments to `~/Desktop/Shipping Quotes/`. Run `markitdown "file.pdf" -o "YYYY-MM-DD Company Quote $X.md"`. Rename the PDF to match. Delete files the user instructs to delete.
3. **Update the table.** Read the `.md` files, extract volume/price/per CBM, and add rows ordered by descending Per CBM (waiting first, rejected last).

## Table rules

- Merge Provider and Email: `**Company Name** - email@example.com`
- Merge Volume and Price: `80 CF (2.27 CBM) / **$2437**`
- Declare defaults once above the table. Delete columns fully covered by the default. Only note deviations in Evaluation.
- No abbreviations. No commas in numbers. CBM first, other units in parentheses. Bold prices.
- YYYY-MM-DD for all dates. Visible separators only (no `<br>`).

## Email

- Never change the subject — reply with `Re: [original subject]`.
- Use `threadId` + `In-Reply-To` headers to stay in the same conversation.
- Check per recipient: "Did this person already receive this content?" before resending.
- CC the owner and any contacts listed in the memory file.
- Gmail API via `~/.google/oauth_token.json` (see email-digest for the Python pattern).

## Memory file

Each sourcing problem has its own memory file with:
- Provider tables with phone, website, quote links, reviews, email, status
- Key references: pickup/delivery addresses, item list URL, contact info
- The process section above the first table (so a new agent can pick up from zero)
