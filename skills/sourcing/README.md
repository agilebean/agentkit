# Sourcing

Sourcing workflow for any provider comparison problem: find vendors, request quotes, check email for replies, maintain comparison tables in `memory/`.

## Triggers

Two trigger phrases, recognized from the skill `description`:

| Trigger | Use when | What happens |
|---|---|---|
| **do sourcing for [problem]** | Starting a new sourcing task | Agent onboards you via the question tool, then searches for providers |
| **update [problem]** | Continuing an existing problem | Agent checks Gmail for replies since the last table update |

The `[problem]` name matches a file in `memory/`. Examples:

- `do sourcing for insurance brokers in Seoul` → new file `memory/insurance_seoul.md`
- `update shipping` → loads `memory/shipping_ca2korea.md`, checks for new quotes

## New problem: onboarding via question tool

When you say **do sourcing for [problem]**, the agent asks:

1. **Working folder** — where to save PDFs and converted `.md` files
2. **Owner email** — for CC on all correspondence (default: `chaehan.so@gmail.com`)
3. **Language of correspondence** — Korean, English, or mixed
4. **Provider type** — what service (determines search directories, certification bodies, table metrics)
5. **Comparison metrics** — which columns to compare. The agent proposes columns based on the provider type; you confirm or adjust. The last column is the normalized comparison metric (Per CBM, $/month, $/unit, etc.)

Answers are stored in the memory file header so the agent can resume later without re-asking.

## Existing problem: update workflow

When you say **update [problem]**, the agent:

1. Loads the memory file (onboarding answers, current tables, contacts)
2. Searches Gmail for messages from each provider email in the Awaiting table, since the last table update
3. Processes each reply:
   - Quote in PDF attachment → converts with `markitdown`, extracts metrics
   - Quote in email body → extracts metrics directly
   - Generic info only → notes in Status, follows up with item list link
   - No reply → Status unchanged
4. Updates the comparison table (waiting at top, descending by normalized metric, rejected last)
5. Reports what changed since last update

## Memory file naming

Name files after the problem, not the workflow: `shipping_ca2korea.md`, not `sourcing_ca2korea.md`. No `sourcing/` folder. A problem may start as a question and become a sourcing problem later — just add the in-file pointer when it does:

```
> Formatting and email rules are in the `sourcing` skill. This file holds only domain data.
```

## What lives where

| Location | Contents |
|---|---|
| **This skill** (`SKILL.md`) | Behavioral rules: process, table formatting, email, Gmail pattern |
| **Memory file** | Domain data: onboarding answers, provider tables, addresses, contacts, key findings |

The skill is the behavior. The memory file is the data.
