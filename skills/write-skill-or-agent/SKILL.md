---
name: write-skill-or-agent
description: Guide the user through writing agent instruction files or skill files. Asks clarifying questions one at a time to resolve ambiguities that would otherwise become prediction-as-prior wording in the instructions. Use when creating or editing agent instructions, skill files, system prompts, or workflow definitions.
---

# Write Bias-Safe Agent and Skill Instructions

When a user describes what an agent or skill should do, do not write the
instructions immediately. The requirement description is always incomplete.
Writing instructions from an incomplete description forces the LLM to fill
gaps with assumptions. Those assumptions become predictions in the instruction
text. Those predictions become priors that cause silent data skips later.

Instead, grill the user with targeted questions until every ambiguity that
could produce a prediction is resolved. Only then write the instructions.

## Phase 1: Grill

Ask questions one at a time using the question tool. Each question targets
a specific class of ambiguity that, if left unresolved, would produce a
prediction in the instruction text.

### Question targets

**Data shape.** For every data source the agent reads (emails, files, API
responses, web pages), ask: "What formats can the data arrive in?" Never
assume the agent knows. If the user says "quotes arrive as PDFs," ask: "Can
a quote also arrive in the email body without a PDF?" If the answer is yes,
the instruction needs a branch for it. If no, the instruction can say so —
but the user confirmed it, not the LLM.

**Completion signals.** For every loop in the workflow ("for each
provider," "for each message"), ask: "What signals that this item is done
and you should move to the next?" If the user says "when I find a quote,"
ask: "Can a follow-up message from the same provider contain a revised
quote without being a new quote?" If yes, "found a quote" is not a
completion signal — the agent must process every message.

**Exception and edge cases.** Ask: "What happens when [step] fails? When
the data is in an unexpected format? When the provider replies from a
different address?" Every exception is a branch. Every branch is an
opportunity for a prediction to sneak in. Resolve them before writing.

**Domain claims.** If the user's description contains a claim about where
data lives ("quotes are in PDFs"), ask: "Is that always true, or is it just
the common case?" If it is always true, the claim can stay as a stated
constraint the user confirmed. If it is just common, it must not appear in
the instruction at all.

**Search and query patterns.** If the workflow involves searching
(Gmail, files, APIs), ask: "What filters should the search use? Are there
filters that must NOT be applied?" If the user says "search after the last
checked date," ask: "Should you also bound the upper date? Could bounding
it exclude recent data?" Resolve the query pattern before writing code
examples.

**Exit conditions.** For every workflow with steps, ask: "What conditions
end the workflow? What happens if a step fails?" A workflow without an exit
condition is a procedural box the agent cannot escape.

### How to ask

Use the question tool. Ask one question at a time. Provide a recommended
answer based on what you know so far, but let the user override. Do not
write any instruction text until the grilling is complete and the user
confirms shared understanding.

If a fact can be found by exploring the codebase (existing agent files,
skill files, memory), look it up rather than asking. The decisions are the
user's. The facts are yours to discover.

## Phase 2: Write

Once all ambiguities are resolved, write the instruction file applying
these principles:

**Actions and conditions, never predictions.** Every branch is defined by
its condition, not by a claim about the data. "If the reply has PDF
attachments:" — no parenthetical. "If the reply has no PDF attachments:" —
no parenthetical. The condition triggers the action. The prediction does
nothing.

**No supplementary framing.** Every action is mandatory and primary. Do
not use "ALSO," "additionally," or "optionally" before an action. If the
action is required, say it directly. "Parse the email body" — not "ALSO
parse the email body."

**No outcome predictions.** Do not state what a result will be before the
action runs. "Check the parsed result. If it contains pricing, add a row.
If not, note as follow-up." — not "this is not a quote, it's a follow-up."

**Simplest code examples.** Use the simplest query that works. Move
filtering into application code. Do not include operators the LLM would
naturally extend. If `after:` is needed, explain that `before:` must not be
added — but only if the grilling confirmed this is a real risk.

**Exit conditions on every workflow.** Every step sequence must define
what ends it and what happens on failure. "If this step fails, stop and
report to the user" — not an implicit assumption that the agent will know
when to stop.

## Phase 3: Self-audit

After writing the draft, re-read it and check for the four error types:

1. **Domain prediction** — any parenthetical, aside, or framing that claims
   where data lives. If present, was this confirmed by the user during
   grilling? If yes, it can stay as a stated constraint. If no, strip it.

2. **Supplementary framing** — any "ALSO," "additionally," or "optionally"
   before a mandatory action. Strip the word.

3. **Outcome prediction** — any sentence that states what a result will be
   before the action runs. Replace with a conditional on the actual result.

4. **Pattern invitation** — any code example with query operators the LLM
   would extend. Simplify or move filtering to application code.

Fix violations before showing the draft to the user.

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
