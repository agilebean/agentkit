---
name: write-skill-or-agent
description: Write or review agent instruction files and skill files to prevent wording that creates LLM priors causing silent data skips. Use when creating, editing, or reviewing agent instructions, skill files, system prompts, or workflow definitions.
---

# Write Bias-Safe Agent and Skill Instructions

When writing or reviewing agent instructions or skill files, the goal is
to prevent wording that creates LLM priors causing silent data skips. The
root cause of agents missing data is usually not a logic error in the
control flow. It is wording in the instruction text that creates a
**prediction** the LLM internalizes as a **prior** before it ever sees the
data. The prior filters out the data the instruction was supposed to catch.

## The principle

Agent instructions should contain **actions and conditions**, never
**predictions about the data**. Every prediction becomes a prior. Every prior
becomes a filter. Every filter skips work when the prediction is wrong. The
LLM cannot override its own priors because they are built during instruction
reading, before data is ever seen.

## Three error types

### Type 1: Domain predictions

Parentheticals, asides, or emphasis that claim where data lives or does not
live. The LLM reads these as facts about the domain, not as heuristics.

**Example:**
```
(this is the common case — quotes are in PDFs, not email bodies)
```
**Forward mechanism:** The LLM internalizes "quotes are in PDFs" as a fact.
Every message without a PDF is pre-classified as "not containing a quote"
before any parsing runs. When a revised price arrives in an email body
without a PDF, the LLM skips it — not because it ignored the instruction,
but because its task model says the message cannot contain a quote.

**Detection:** Look for parentheticals on branch headings, "this is the
common case" framing, "X is in Y, not Z" assertions. For each, ask: "Is
this always true? Can the opposite case occur?" If yes, the wording is a
prediction.

**Fix:** Strip the parenthetical. The branch condition ("if the reply has
PDF attachments") is sufficient. The prediction adds nothing to the action
and everything to the prior.

### Type 2: Outcome predictions

Instructions that state the expected result of an action before the action
runs. The LLM enters the action already expecting the predicted outcome
and accepts weak or partial results as confirmation.

**Example:**
```
If parsed["volume_price"] is empty, this is not a quote — it's a
follow-up or info email.
```
**Forward mechanism:** The instruction tells the LLM the result before the
parse runs. When `parse_quote` returns a weak result (e.g., for Korean text
it doesn't recognize), the LLM accepts the empty result as the expected
outcome rather than investigating. The instruction provided the conclusion
before the evidence.

**Detection:** Look for "this is not X" or "this means Y" language attached
to a check. For each, ask: "Does this sentence describe what the result
IS, or what it SHOULD BE?" If the latter, it is a prediction.

**Fix:** Replace with a conditional action based on the actual result:
"Check the parsed result. If it contains pricing information, add a row.
If not, note it as a follow-up." The action is the same. The prediction is
gone.

### Type 3: Pattern invitations

Code examples or templates that establish query patterns the LLM will
extend without being told to.

**Example:**
```python
results = backend.search_messages(f"from:{email} after:{date}", max_results=10)
```
**Forward mechanism:** The LLM generalizes: if `after:` is a lower bound,
`before:` is an upper bound. It adds `before:2026/07/09` to narrow the
search, silently cutting off the most recent day — the day a revised quote
arrived. The LLM is not overriding the instruction; it is extending a pattern
the instruction established.

**Detection:** Look for code examples with query operators, flag patterns,
or CLI arguments. For each, ask: "Would the LLM naturally extend this
pattern? What would the extension look like, and would it be harmful?"

**Fix:** Use the simplest possible example that does not invite extension.
Move filtering into application code (Python) rather than query syntax. If
the example must use operators, explicitly state what must NOT be added.

## Audit method

1. Read the instruction file. Extract every:
   - Parenthetical aside on a heading or branch
   - "This is the common case" / "this is not X" framing
   - Predicted outcome stated before an action runs
   - Code example with query operators or patterns

2. For each extraction, trace the forward pass: what task model does the
   LLM build from this wording before it sees any data? What does the LLM
   pre-classify as irrelevant?

3. For each, ask: "What happens when this prediction is wrong?" If the
   answer is "the LLM skips data it should have processed," the wording is
   a prediction that must be stripped.

4. Fix by stripping the prediction, not by reordering the control flow.
   The action stays. The prediction goes. If the prediction encodes a
   genuine domain constraint that the user must confirm, ask the user
   before stripping — do not assume.

## Nuance: what helps and what doesn't

### Control flows

Control flows are not inherently bad. A well-structured if/else branch with
clear conditions helps the LLM route correctly. The danger is when a control
flow fixates the scope — when the branching tells the LLM "this is the only
shape the data can take" instead of "if the data has this shape, do this."

The distinction: a condition ("if the reply has PDF attachments") is an
action trigger. A prediction on a condition ("quotes are in PDFs, not email
bodies") is a scope fixation. Conditions are fine. Predictions on conditions
are not.

When a workflow is complex enough that a control flow helps the LLM navigate,
the control flow should describe what to DO in each branch, not what the data
WILL BE. "If PDF: download, convert, parse" is fine. "If PDF (this is where
quotes live): download, convert, parse" is not.

If the workflow is simple enough that the LLM can infer the branching from
conditions alone, do not add a control flow at all. Every branch is an
opportunity for a prediction to sneak in.

### Prohibitions

Prohibitions ("never add before:") are weak against the LLM's optimization
drive. The LLM will find a different shortcut around the prohibition. They
have a place — as guardrails after the prediction is stripped, not as the
primary fix. Fix the wording that creates the prior first. Add a prohibition
only if the LLM has repeatedly extended a pattern in the same direction.

### Failure examples

Failure examples are useful when they are correct and generalizable. They
are harmful when they are specific to one instance and the LLM overfits to
that instance. The test: "If I remove this example, does the LLM still
understand the principle?" If yes, the example is supplementary. If no, the
example is doing the work of the principle, and the principle is too weak.

One example per error type, grounded in the principle, is enough. Ten
examples of specific failures teach the LLM to pattern-match against those
cases rather than understand the principle.

## When to verify with the user

When an instruction makes a domain claim (e.g., "quotes are in PDFs"),
do not assume the claim is wrong and strip it silently. Ask the user:
"Your instruction says '{exact wording}'. Is this always true, or can
the opposite case occur?" If the user confirms it is always true, the
claim can stay. If not, the claim is a prediction that must be stripped
or made conditional.

This is the key differentiation from a static linter: the audit asks the
user about domain facts it cannot determine from the instruction text
alone. The instruction author knows whether "quotes are in PDFs" is a
domain constraint or a convenience assumption. The LLM does not.
