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

## Why this matters: how predictions become silent failures

An LLM reads instruction text and builds a task model before it sees any
data. Every prediction in the text becomes a fact in that model. Every fact
becomes a filter. Every filter skips data when the prediction is wrong. The
LLM cannot override its own priors because they are built during instruction
reading, before data is ever seen.

Four error types cause this. Each is a way of writing an instruction that
seems helpful but creates a prior the LLM cannot escape.

### Error type 1: Domain prediction

A parenthetical or aside claiming where data lives or does not live. The
LLM reads it as a domain fact, not as a heuristic.

Example: an instruction branch heading says "(data arrives as JSON, not
XML)." The LLM internalizes "data is JSON" as a fact. When XML arrives, the
LLM does not parse it because its task model says it cannot exist. The LLM
did not ignore the instruction. It followed the prediction the instruction
made.

Detection: Look for parentheticals on branch headings, "this is the common
case" framing, "X is in Y, not Z" assertions. For each, ask: "Is this
always true? Can the opposite case occur?" If yes, the wording is a
prediction.

Fix: Strip the parenthetical. The branch condition ("if the data is JSON")
is sufficient. The prediction adds nothing to the action and everything to
the prior.

### Error type 2: Supplementary framing

A word that makes a mandatory action look optional. The LLM treats the
action as enhancement, not requirement. Under cognitive load, the
enhancement is dropped.

Example: an instruction says "ALSO check the error log." "ALSO" marks
error-log checking as secondary to the primary task. When the LLM's
attention is spread across many items, it completes the primary task and
drops the supplementary one. The word "ALSO" made a mandatory action look
optional.

Detection: "ALSO", "additionally", "optionally", "as a bonus" before an
action. For each, ask: "Is this action mandatory?" If mandatory, the word
is lying about the action's status.

Fix: Remove the word. "Check the error log" is the instruction. "ALSO
check the error log" is a suggestion.

### Error type 3: Outcome prediction

A sentence stating the expected result of an action before the action runs.
The LLM enters the action expecting that outcome and accepts ambiguous or
weak results as confirmation.

Example: an instruction says "if the field is empty, the record was
deleted." The instruction states the conclusion before the evidence. When
the field is empty due to a parsing error (not a deletion), the LLM accepts
the empty result as the expected outcome rather than investigating. The
instruction provided the conclusion before the evidence.

Detection: "this is not X" or "this means Y" language attached to a check.
For each, ask: "Does this sentence describe what the result IS, or what it
SHOULD BE?" If the latter, it is a prediction.

Fix: Replace with a conditional on the actual result. "Check the field.
If it is empty, investigate whether the record was deleted or the parse
failed." The action is the same. The prediction is gone.

### Error type 4: Pattern invitation

A code example or template establishing a query pattern the LLM extends
without being told to. The extension is not in the instruction and may be
harmful.

Example: a search template uses `query after:{date}`. The LLM generalizes:
if `after:` is a lower bound, `before:` is an upper bound. It adds
`before:` to narrow the search, silently cutting off recent data. The LLM
is not overriding the instruction. It is extending a pattern the instruction
established.

Detection: code examples with query operators, flag patterns, CLI
arguments. For each, ask: "Would the LLM naturally extend this pattern?
What would the extension look like, and would it be harmful?"

Fix: Use the simplest example that does not invite extension. Move
filtering into application code rather than query syntax. If the example
must use operators, explicitly state what must NOT be added.

## Phase 1: Grill

Ask questions one at a time using the question tool. Each question targets
a specific class of ambiguity that, if left unresolved, would produce one
of the four error types above. Provide a recommended answer based on what
you know so far, but let the user override.

If a fact can be found by exploring the codebase (existing agent files,
skill files, memory), look it up rather than asking. The decisions are the
user's. The facts are yours to discover.

### What to ask about

**Data shape (prevents domain predictions).** For every data source the
agent reads (emails, files, API responses, web pages), ask: "What formats
can the data arrive in?" If the user says "data arrives as JSON," ask: "Can
it also arrive in another format?" If yes, the instruction needs a branch
for it. If no, the user confirmed it. The LLM did not assume it.

**Completion signals (prevents supplementary framing drops).** For every
loop in the workflow ("for each item," "for each message"), ask: "What
signals that this item is done and you should move to the next?" If the
user says "when I find a result," ask: "Can a follow-up item from the same
source contain a revised result?" If yes, "found a result" is not a
completion signal. The agent must process every item.

**Expected results (prevents outcome predictions).** For every check or
parse step, ask: "What can the result look like? Can it be partial or
ambiguous?" If yes, the instruction must not state what the result will be
before the action runs. It must say "check the result and decide based on
what you find."

**Query patterns (prevents pattern invitations).** If the workflow involves
searching (Gmail, files, APIs), ask: "What filters should the search use?
Are there filters that must NOT be applied?" If the user says "search after
a date," ask: "Should you also bound the upper date? Could bounding it
exclude recent data?" Resolve the query pattern before writing code
examples. Use the simplest query that works. Move filtering into
application code.

**Exception and edge cases.** Ask: "What happens when [step] fails? When
the data is in an unexpected format? When the source replies from a
different address?" Every exception is a branch. Every branch is an
opportunity for a prediction to sneak in. Resolve them before writing.

**Exit conditions.** For every workflow with steps, ask: "What conditions
end the workflow? What happens if a step fails?" A workflow without an exit
condition is a procedural box the agent cannot escape.

### How to ask

Use the question tool. Ask one question at a time. Do not write any
instruction text until the grilling is complete and the user confirms
shared understanding.

## Phase 2: Write

Once all ambiguities are resolved, write the instruction file applying
these principles:

**Actions and conditions, never predictions.** Every branch is defined by
its condition, not by a claim about the data. "If the data is JSON:" not
"If the data is JSON (this is the common case)."

**No supplementary framing.** Every action is mandatory and primary. Do
not use "ALSO," "additionally," or "optionally" before a mandatory action.

**No outcome predictions.** Do not state what a result will be before the
action runs. "Check the result. If it contains the expected fields,
proceed. If not, investigate."

**Simplest code examples.** Use the simplest query that works. Move
filtering into application code. Do not include operators the LLM would
naturally extend.

**Exit conditions on every workflow.** Every step sequence must define
what ends it and what happens on failure. "If this step fails, stop and
report to the user."

## Phase 3: Self-audit

After writing the draft, re-read it and check for the four error types:

1. **Domain prediction** — any parenthetical or aside claiming where data
   lives. If not confirmed by the user during grilling, strip it.

2. **Supplementary framing** — any "ALSO," "additionally," or "optionally"
   before a mandatory action. Strip the word.

3. **Outcome prediction** — any sentence stating what a result will be
   before the action runs. Replace with a conditional on the actual result.

4. **Pattern invitation** — any code example with query operators the LLM
   would extend. Simplify or move filtering to application code.

Fix violations before showing the draft to the user.

## Nuance

### Control flows

Control flows are not inherently bad. A well-structured if/else branch with
clear conditions helps the LLM route correctly. The danger is when a
control flow fixates the scope: when the branching tells the LLM "this is
the only shape the data can take" instead of "if the data has this shape,
do this."

A condition ("if the data has a PDF attachment") is an action trigger. A
prediction on a condition ("data is always in PDFs") is a scope fixation.
Conditions are fine. Predictions on conditions are not.

When a control flow helps the LLM navigate, it should describe what to DO
in each branch, not what the data WILL BE. "If PDF: download, convert,
parse" is fine. "If PDF (this is where data lives): download, convert,
parse" is not.

### Prohibitions

Prohibitions are weak against the LLM's optimization drive. The LLM will
find a different shortcut around the prohibition. They have a place as
guardrails after the prediction is stripped, not as the primary fix. Fix
the wording that creates the prior first.

### Failure examples

Failure examples in instructions must be abstracted from the specific past
incident to the general pattern. A specific example ("quotes are in PDFs,
not email bodies") teaches the LLM to pattern-match against that one case.
An abstracted example ("a parenthetical claiming where data lives") teaches
the LLM to recognize the pattern in any future case.

The test: "Does this example teach the principle, or does it teach the
specific instance?" If the example only makes sense in the context of the
original failure, it overfits. If it makes sense in any context where the
same error type could occur, it generalizes.

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
