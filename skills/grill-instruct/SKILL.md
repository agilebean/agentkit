---
name: grill-instruct
description: Guide the user through writing agent instruction files or skill files. Asks clarifying questions one at a time to resolve ambiguities that would otherwise become prediction-as-prior wording causing silent data skips. Use when creating, editing, or reviewing agent instructions, skill files, system prompts, or workflow definitions.
---

# Grill-Instruct: Write Bias-Safe Agent and Skill Instructions

When a user describes what an agent or skill should do, do not write the
instructions immediately. The requirement description is always incomplete.
Writing instructions from an incomplete description forces the LLM to fill
gaps with assumptions. Those assumptions become predictions in the
instruction text. Those predictions become priors that cause silent data
skips later. The LLM cannot override its own priors because they are built
during instruction reading, before data is ever seen.

Instead, grill the user with targeted questions until every ambiguity that
could produce a prediction is resolved. Only then write the instructions.

## Why this matters: a real failure

An evernote-shipping agent was instructed to check Gmail for shipping quote
replies and update an Evernote table. The instruction had this branching:

```
If the reply has PDF attachments (this is the common case — quotes
are in PDFs, not email bodies):
    1. Download PDF, convert, parse
    2. ALSO parse the email body for corrections

If the reply has NO PDF attachments (quote is inline, or it's a
follow-up without a new quote):
    1. Parse the email body
    2. If parsed["volume_price"] is empty, this is not a quote —
       it's a follow-up. Note it but do not add a row.
```

The agent searched Riham, found a Jul 8 PDF ($3,220), parsed it, added the
row, moved on. A Jul 9 follow-up email with no PDF contained a revised price
of $3,000 in the email body. The agent never parsed it. It also added
`before:2026/07/09` to its Gmail search, excluding the day the revised
quote arrived.

Four elements in the instruction text caused this, each a different error
type. Understanding these is necessary to write instructions that do not
repeat them.

### Error type 1: Domain prediction

The PDF branch heading said "(this is the common case — quotes are in PDFs,
not email bodies)." The LLM internalized "quotes are in PDFs" as a domain
fact. Every message without a PDF was pre-classified as "not containing a
quote" before any parsing ran. When a revised price arrived in an email body
without a PDF, the LLM skipped it — not because it ignored the instruction,
but because its task model said the message cannot contain a quote.

**The forward mechanism:** The LLM reads instruction text and builds a task
model before it sees any data. A parenthetical claiming where data lives
becomes a fact in the task model. That fact becomes a filter. That filter
skips data when the claim is wrong. The LLM cannot override this because the
filter was built during instruction reading, before data was ever seen.

### Error type 2: Supplementary framing

Step 4 said "ALSO parse the email body." "ALSO" marked email body parsing as
secondary to the PDF. The PDF was the primary source. Under cognitive load
(many providers, many messages), the supplementary task had no clear
completion signal and was dropped.

**The forward mechanism:** "ALSO" tells the LLM this action is optional
enhancement. When the LLM's attention is spread across many items, it
completes the primary task (parse the PDF) and drops the supplementary task
(parse the body). The word "ALSO" made a mandatory action look optional.

### Error type 3: Outcome prediction

The non-PDF branch said "If parsed['volume_price'] is empty, this is not a
quote — it's a follow-up." The instruction stated the conclusion before the
evidence. The LLM entered the parse already expecting an empty result and
accepted weak parses (Korean text the parser did not recognize) as
confirmation.

**The forward mechanism:** When an instruction tells the LLM what the
result will be, the LLM treats that as the expected outcome. When the actual
result is ambiguous (the parser returns partial or weak data), the LLM
rounds to the expected outcome rather than investigating. The instruction
provided the conclusion before the evidence.

### Error type 4: Pattern invitation

The search template used `from:{email} after:{date}`. The LLM generalized:
if `after:` is a lower bound, `before:` is an upper bound. It added
`before:2026/07/09` to narrow the search, silently cutting off the most
recent day — the day the revised quote arrived.

**The forward mechanism:** Code examples in instructions are not just
illustrations. They are patterns the LLM extends. If the example uses
`after:`, the LLM infers `before:` is also available. If the example uses
`-v`, the LLM infers `-vv` is also available. The LLM is not overriding the
instruction; it is extending a pattern the instruction established.

### The principle

Agent instructions should contain **actions and conditions**, never
**predictions about the data**. Every prediction becomes a prior. Every
prior becomes a filter. Every filter skips work when the prediction is
wrong.

## Phase 1: Grill

Ask questions one at a time using the question tool. Each question targets
a specific class of ambiguity that, if left unresolved, would produce one
of the four error types above in the instruction text. Provide a recommended
answer based on what you know so far, but let the user override.

If a fact can be found by exploring the codebase (existing agent files,
skill files, memory), look it up rather than asking. The decisions are the
user's. The facts are yours to discover.

### What to ask about

**Data shape (prevents domain predictions).** For every data source the
agent reads (emails, files, API responses, web pages), ask: "What formats
can the data arrive in?" If the user says "quotes arrive as PDFs," ask: "Can
a quote also arrive in the email body without a PDF?" If yes, the
instruction needs a branch for it. If no, the user confirmed it — the LLM
did not assume it.

**Completion signals (prevents supplementary framing drops).** For every
loop in the workflow ("for each provider," "for each message"), ask: "What
signals that this item is done and you should move to the next?" If the user
says "when I find a quote," ask: "Can a follow-up message from the same
provider contain a revised quote?" If yes, "found a quote" is not a
completion signal — the agent must process every message.

**Expected results (prevents outcome predictions).** For every check or
parse step, ask: "What can the result look like? Can it be partial or
ambiguous?" If yes, the instruction must not state what the result will be
before the action runs. It must say "check the result and decide based on
what you find" — not "this is not a quote."

**Query patterns (prevents pattern invitations).** If the workflow involves
searching (Gmail, files, APIs), ask: "What filters should the search use?
Are there filters that must NOT be applied?" If the user says "search after
the last checked date," ask: "Should you also bound the upper date? Could
bounding it exclude recent data?" Resolve the query pattern before writing
code examples. Use the simplest query that works. Move filtering into
application code.

**Exception and edge cases.** Ask: "What happens when [step] fails? When
the data is in an unexpected format? When the provider replies from a
different address?" Every exception is a branch. Every branch is an
opportunity for a prediction to sneak in. Resolve them before writing.

**Exit conditions.** For every workflow with steps, ask: "What conditions
end the workflow? What happens if a step fails?" A workflow without an exit
condition is a procedural box the agent cannot escape.

### How to ask

Use the question tool. Ask one question at a time. Do not write any
instruction text until the grilling is complete and the user confirms shared
understanding.

## Phase 2: Write

Once all ambiguities are resolved, write the instruction file applying
these principles. For each, the rule and the concrete evernote failure that
motivates it:

**Actions and conditions, never predictions.** Every branch is defined by
its condition, not by a claim about the data. Write "If the reply has PDF
attachments:" — not "If the reply has PDF attachments (this is the common
case — quotes are in PDFs, not email bodies):" The parenthetical became a
prior that caused the LLM to skip email-body quotes.

**No supplementary framing.** Every action is mandatory and primary. Write
"Parse the email body" — not "ALSO parse the email body." "ALSO" made a
mandatory action look optional and the LLM dropped it under cognitive load.

**No outcome predictions.** Do not state what a result will be before the
action runs. Write "Check the parsed result. If it contains pricing, add a
row. If not, note as follow-up." — not "this is not a quote, it's a
follow-up." The prediction made the LLM accept weak parses as confirmation
of the expected empty result.

**Simplest code examples.** Use the simplest query that works. Move
filtering into application code. Do not include operators the LLM would
naturally extend. The `after:{date}` template invited the LLM to add
`before:{date}`, which silently excluded the day a revised quote arrived.

**Exit conditions on every workflow.** Every step sequence must define what
ends it and what happens on failure. A workflow that says "follow these
steps" without saying what to do when a step fails is a procedural box with
no exit hatch.

## Phase 3: Self-audit

After writing the draft, re-read it and check for the four error types.
Each check includes the concrete failure that motivates it:

1. **Domain prediction** — any parenthetical, aside, or framing that claims
   where data lives. Ask: "If this claim is wrong, what data gets skipped?"
   In the evernote case, "quotes are in PDFs" skipped email-body quotes. If
   the claim was not confirmed by the user during grilling, strip it.

2. **Supplementary framing** — any "ALSO," "additionally," or "optionally"
   before a mandatory action. Ask: "Is this action mandatory?" In the
   evernote case, "ALSO parse the email body" caused the LLM to drop email
   body parsing under cognitive load. If the action is mandatory, strip the
   word.

3. **Outcome prediction** — any sentence that states what a result will be
   before the action runs. Ask: "Does this sentence describe what the result
   IS, or what it SHOULD BE?" In the evernote case, "this is not a quote"
   made the LLM accept weak parses as confirmation. Replace with a
   conditional on the actual result.

4. **Pattern invitation** — any code example with query operators the LLM
   would extend. Ask: "Would the LLM naturally extend this pattern?" In the
   evernote case, `after:{date}` invited `before:{date}`. Simplify or move
   filtering to application code.

Fix violations before showing the draft to the user.

## Nuance

### Control flows

Control flows are not inherently bad. A well-structured if/else branch with
clear conditions helps the LLM route correctly. The danger is when a control
flow fixates the scope — when the branching tells the LLM "this is the only
shape the data can take" instead of "if the data has this shape, do this."

A condition ("if the reply has PDF attachments") is an action trigger. A
prediction on a condition ("quotes are in PDFs, not email bodies") is a
scope fixation. Conditions are fine. Predictions on conditions are not.

When a workflow is complex enough that a control flow helps the LLM
navigate, the control flow should describe what to DO in each branch, not
what the data WILL BE. "If PDF: download, convert, parse" is fine. "If PDF
(this is where quotes live): download, convert, parse" is not.

### Prohibitions

Prohibitions ("never add before:") are weak against the LLM's optimization
drive. The LLM will find a different shortcut around the prohibition. They
have a place — as guardrails after the prediction is stripped, not as the
primary fix. Fix the wording that creates the prior first. Add a prohibition
only if the LLM has repeatedly extended a pattern in the same direction.

### Failure examples

Failure examples are useful when they are correct and generalizable. They
are harmful when they are specific to one instance and the LLM overfits to
that instance. One example per error type, grounded in the principle, is
enough. Ten examples of specific failures teach the LLM to pattern-match
against those cases rather than understand the principle.

The test: "If I remove this example, does the LLM still understand the
principle?" If yes, the example is supplementary. If no, the example is
doing the work of the principle, and the principle is too weak.

## When this skill applies

Use when the user says any of:
- "write an agent that..."
- "create a skill for..."
- "update the agent instructions..."
- "fix the agent that missed..."
- or describes a workflow an agent should perform

Do not use for:
- Writing application code (use TDD skill)
- Stress-testing a plan (use grill-me)
- Creating issues from a plan (use to-issues)
