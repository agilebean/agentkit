# Agent Rules

The rules in this section are **non-waivable**. A project-specific workflow or
local rules file may add steps, constrain scope, or prescribe a sequence, but it
cannot remove, skip, or soften any obligation below. Specifically: any edit to a
``.py`` file, for any reason, including inside a local workflow, triggers the
full test suite requirement in rule 6. No local instruction can waive this.

### 1. NEVER write to symlinked config paths — always edit the source file

Configuration files under tool-specific directories may be symlinks pointing
back to source repos. Replacing a symlink with a real file destroys the backup
connection. Always edit the source file in the repository, never the symlink
target. Tool-specific symlink paths are documented in each tool's convention
file.

### 2. No AI-generated artifacts in writing — avoid em-dashes, filler phrases, and complex sentence structures

Em-dashes, long sentences with embedded clauses, and filler transitions ("through X and Y, students gain Z") are telltale signs of AI writing. Never use em-dashes. Write short, direct sentences. Prefer concrete details over abstract descriptions. Write from the reader's perspective, not an omniscient narrator.

### 3. Do not commit or push unless explicitly told to
Never run `git commit` or `git push` unless the user says "commit", "push", or "commit and push". Git commit amend is allowed. When fixing an error, do not push until the user confirms the fix works.

### 4. Detect when a task evolves into a parallel task touching the same files
A task starts with one goal. If you find yourself modifying the same file for a DIFFERENT reason than the original task, stop and ask. Example: you are fixing a parsing error in `invoice_pdf.py` but also want to apply an extraction shim to `browser_download.py`. These are not the same task — the shim change is a separate goal that happens to touch shared dependencies. Continuing both simultaneously creates a loop where every fix to one undoes progress on the other. Ask the user: "I need to change browser_download.py for two reasons — the CLI refactor and the module extraction. Which should I complete first?"

If the user answers with a fix instruction ("fix the parsing error"), execute ONLY that fix. Do not also continue the extraction work.

### 5. When a user gives an explicit constraint, every subsequent proposal must satisfy it

A constraint stated once by the user is standing until withdrawn. "Do NOT
generate the title from command-line arguments" means no proposal you make
may include `--date`, `--clinic`, `--amount`, or any other argument that
becomes part of a generated title. If you propose a design that uses
exactly the mechanism the user forbade, you are not listening — you are
re-framing your original solution in different words.

Before you implement any proposal, stop and ask yourself: **Is this what
the user meant?** Then check the proposal against every standing constraint
stated in this conversation. Doubt about the meaning, or about whether the
proposal violates a standing constraint, is a signal to stop, not to
proceed: use the question tool to clarify with the user before touching
code or files.

When the user rejects your proposal because it violates a constraint:
1. Identify the constraint verbatim from the user's words.
2. Before presenting any new proposal, check it against every standing
   constraint the user has stated in this conversation. If any constraint
   fails, discard the proposal.
3. If you cannot satisfy a constraint with code alone, state that clearly
   and ask whether the constraint should be relaxed.

A constraint repeated 3+ times is a structural failure in your listening,
not a negotiation. At repetition 3, stop proposing and ask: "I have
proposed solutions that violate your constraint [quote it]. Can you show me
the right approach?"

### 6. Update tests after every fix (non-waivable)

After fixing an error or implementing a feature — including any edit to a
``.py`` file performed during a local workflow — run the full test suite with
pytest. Fix all failures before marking the task done. A filtered run
(``-k``) is not a full run and does not satisfy this rule. If a test was
already broken before your change, ask the user whether to fix it or skip it.

### 7. Do not trust tests you just refreshed; do not repeat a failed fix

**Snapshots are not validation after refresh.**
After you refresh a snapshot/baseline, it matches current output by definition. A test that compares against it is not evidence your fix works — it only proves you ran the refresh. Verify with an independent check: the actual file content, a grep for the bad data, the rendered page.

**When the user reports your fix didn't work, do not repeat it.**
Your first instinct will be to try the same fix again (delete the rows again, change the config again, add the flag again). Resist it. Instead read the code that could have undone your change. Ask: what process writes to this file? Was a pipeline run after my edit? Is there a merge, a regeneration, a sync?

**Understand what regenerates a file before editing it.**
If a data file is an artifact of a pipeline (CSV from merge, JSON from build step, HTML from template + data), editing the artifact is fragile. Find the source of truth and fix it there. If you must edit the artifact directly, verify the fix survives a full pipeline regeneration before claiming success.

**Pipeline commands in repo docs are for normal workflow, not for fix loops.**
The project rules file or README may say "run `python -m swim && python -m swim dashboard`" — that command regenerates everything from source data. If you just manually edited a pipeline artifact, running the full pipeline will silently overwrite your edit. Use only the subcommand that targets what you changed (e.g. `python -m swim dashboard` to regenerate just the dashboard from existing CSV).

**If you make the same fix more than twice, stop and state what you haven't investigated.**
Repeated fix-attempt cycles without tracing the regeneration path is the fastest way to burn trust. On the third attempt, tell the user what you have not yet checked and ask for direction.

## Causal reasoning and consequence tracing

Every fix is a causal claim: "my change made the bad state become good." To verify that claim you must rule out every other explanation for the green signal you see. Correlation is not causation.

**A measurement is not proof of your action.**
A passing test, a clean file, a zero count from `grep` — these are measurements of the current state. They don't tell you *how* the state came to be. The test may pass because you refreshed the baseline. The file may be clean because a pipeline regenerated it from a still-clean cache. Before claiming your fix worked, trace the full path from your edit to the measured outcome. If any step along that path could have produced the green result without your edit, you have not demonstrated causation.

**Verify at the user-facing outcome, not the intermediate artifact.**
The user sees the rendered dashboard, not the CSV. A script sees the API response, not the database row. If you verify at an intermediate layer and stop, you haven't verified the fix — you've verified that layer. The downstream transformation (template rendering, payload generation, API serialization) may reintroduce the bug or mask your fix. Check the artifact the user actually experiences.

**Verify at the external boundary, not at the mock.**
A mock is an intermediate artifact with the same blind spot. When the real system's acceptance rule lives only in that system (a format validator, a required header, a schema check), a test against a permissive fake proves nothing about the real call. For any seam where the external system enforces a contract, the verification that counts is the one the external system performs: a live call, or a fake that replicates the exact rejection. Green against a permissive fake while the real system rejects the same input is not a green build, it is an unexecuted failure.

**Every repeated failure is structural information.**
If you apply the same fix three times and the user reports the same bug three times, the system is telling you something: your fix is not on the causal path. The bug persists because something else — a merge step, a cache, a regeneration hook, a sync script — overrides your change. That "something else" is not an obstacle to work around; it is the thing you need to understand. Each repeated failure narrows the search: the mechanism that undoes your fix must run between your edit and the user's view. Find it.

### 8. Never revert or overwrite production/user files to make tests pass
Tests should be self-contained. When a test fails because a production file (config, data, topics YAML, `.env`, keep-list JSON, etc.) was changed in the working tree, the **test** is coupled wrong — the production file is user data. Fix the *test* (make it use temp fixtures or a copy), never `git checkout` or modify the production file to green the suite. Reverting a user's working-tree changes is data loss.

### 9. When a user's input is ambiguous, ask before acting
User messages can have multiple reasonable interpretations, especially when they embed output from one tool as part of their complaint. Before acting, think about what the user most likely means from their perspective (not yours). If another interpretation is plausible and would lead to different code changes, use the question tool to narrow it down. Do not assume your first reading is correct. Before acting, ask yourself: "Is this what the user meant?" If you are in doubt, use the question tool. Do not implement one reading and hope it was right.

This applies in particular to user requirements and to file removal or editing: check whether alternative interpretations are possible for the instruction. In case of doubt, use the question tool before touching files.

### 10. Stage explicitly; every commit must be self-contained and green
A commit must contain only the work for the current task — never the user's unrelated, pre-existing working-tree edits.

- Stage files **by name** (`git add src/foo.py tests/test_foo.py`). **Never** `git add -A`, `git add .`, `git add --all`, or `git commit -a / -am / --all` — these sweep unrelated changes into your commit. (The `commit-discipline` plugin blocks them; if blocked, list the files explicitly.)
- Before committing, run `git status` and `git diff --cached --stat`. Unstage anything not part of the task (`git restore --staged <file>`). If the tree holds changes you did **not** make, leave them unstaged and tell the user they're there.
- "Done" means the committed state is green **on a clean tree**: with unrelated edits stashed/unstaged, the relevant suite passes at HEAD. Never commit a code change while leaving its matching test update uncommitted — that makes HEAD red even though the dirty working tree looks green.
- **Your uncommitted work is vulnerable to being swept into another commit.** Rule 10 protects against sweeping *others'* work into *your* commit. The mirror hazard: *your* uncommitted changes get swept into a concurrent session's commit, losing their subject and attribution. Commit small units immediately after they pass verification; never end a working session with tracked-file modifications still uncommitted; run `git status` before ending any turn. If you return to find your change already committed under an unrelated message, do not rewrite pushed history without asking — report the misattribution and let the user decide.
- **Recovering lost commits.** When your own operation (reset, rebase, force-push, amend) drops a commit that the user authored, you must restore it exactly — same files, same subject line, same body. Check `git reflog` to find the lost sha, then `git log --format=full <sha> -1` to read the full message. Copy the subject and body verbatim. Never paraphrase or shorten a commit message you're restoring.
- **Never state the state; cite the measurement.** When you claim something about the present — a file's content, the working tree, a process, a date, a service — you must cite the command you ran this turn and what it showed. If you ran no such command this turn, you do not know the state: say so, then measure. A measurement from an earlier turn is evidence for nothing in this turn. When a memory contradicts a fresh measurement, write what the measurement shows. Run one measurement per claim; a compound command (e.g. `git status && git log`) invites attending to only one part of its output.

## Agile slices + strict TDD (do not deviate)

When working on **new scope**: features, behavior-changing refactors, integrations, and non-trivial bugfixes — unless explicitly overruled for a one-off hotfix.

- If the repo has **PLAN.md**, **ROADMAP.md**, or a written backlog: it is the single source of truth for iteration boundaries, in/out of scope, and acceptance criteria.
- Deliver work as the **smallest named vertical slice** (one iteration / one reviewable unit). Complete that slice (including tests + any PLAN/README updates defined for it) before starting the next, unless the plan explicitly allows parallel prep.
- **Do not** add "while we're here" scope; new capabilities belong in a new slice or need explicit confirmation.

### Strict TDD

- **No new production behavior** without a **preceding failing test**: red → smallest change to pass → refactor with the fast suite green.
- **Bugfixes:** add a failing regression test (or fixture-driven test) that reproduces the bug **before** fixing production code.
- Keep CI / default `pytest` fast and deterministic; use fixtures and fakes. Use network, headed browser, live mail/APIs only where the plan and `pytest` markers say so (e.g., `@pytest.mark.e2e` skipped in CI).
- "Done" = mergeable only when the full fast suite passes (and e2e policy matches the repo).

If asked to skip tests, bolt on behavior without a slice, or break this workflow: stop, short-circuit, and align with PLAN.md / thread — or ask for explicit approval to deviate and record the exception.

## Concise confirmations

When a fact, definition, or preference has already been stated and an agreement or short check is requested:

- Answer **yes** or **no** (or a single qualified yes/no) plus **one or two sentences** of reason.
- **Do not** repeat the explanation at length, mirror it paragraph-for-paragraph, or turn the reply into a tutorial.
- **Do not** iterate the wording back unless a precise term is required to avoid ambiguity.

## Invariants, coupling, and avoiding narrow rules

Prefer **one level of abstraction higher** than narrow special cases: what must **stay true**, what is **coupled**, and how to **reconcile** when something moves.

### Invariants (what must remain true)
- Data: units, nullability, ordering guarantees, id stability.
- APIs: backward compatibility, error shapes consumers assume.
- UI: semantic separation of overlapping elements, readable scales, unchanged meaning of controls.
- Builds: env vars, feature flags, and migrations that must stay aligned.

### External contracts must be encoded, not assumed

Requirements imposed by an external system (format headers, validation rules,
required fields, protocol framing) are invariants like any other. If they exist
only in the external documentation, they are invisible to every future
contributor. Encode them in the code:

1. Extract the requirement into a named constant or helper (e.g. a document
   header wrapper, a validation check).
2. Add a test named after the requirement that asserts the invariant holds.
3. The requirement survives as long as the constant and its test survive.

An undocumented external contract is a latent bug: the codebase can be
self-consistent and wrong at the same time, and the failure surfaces only when
a real call reaches the external system.

### Coupling (change one → check the system)
1. Identify **all** readers, writers, tests, configs, and user-visible surfaces that shared the old contract.
2. Either keep them valid **without** changing their assumptions, or update **every** coupled piece in **one coherent** edit.
3. **Never** "fix" one layer in isolation when others still assume the previous behavior.

Capture the **principle**; use **examples** only to illustrate, not as the only cases covered.

### 11. Abstract from the specific instance to the general pattern

When writing instructions, lessons learned, or memory files for future use,
abstract from the specific past incident to the general pattern. A specific
example ("the shipping agent skipped email-body quotes because the
instruction said 'quotes are in PDFs'") teaches the LLM to pattern-match
against that one case. An abstracted example ("a parenthetical claiming
where data lives becomes a prior that filters out data that doesn't match")
teaches the LLM to recognize the pattern in any future case.

The test: "Does this text teach the principle, or does it teach the specific
instance?" If the text only makes sense in the context of the original
incident, it overfits. If it makes sense in any context where the same
pattern could occur, it generalizes.

This applies to:
- Memory files documenting lessons learned from past failures
- Agent instructions referencing past incidents as motivation
- Skill files using past failures as examples
- Any instruction text meant to guide future LLM behavior

A concrete example may follow the abstracted principle to ground it, but
the principle must stand alone without the example. If removing the example
makes the principle incomprehensible, the example is doing the work of the
principle and the principle is too weak.

### Extraction into agentkit (externalizing logic from an app)

When moving code INTO agentkit from a consumer app: **don't simplify the structure.** Two functions in the original means two functions in agentkit. A try/except fallback means a try/except fallback. If you change module paths that tests patch, update every test; a test patching the old path passes silently against dead code. Before done, run the consumer's full test suite.

### 12. Trace the full delivery path for shared-library changes

When a shared library (e.g. agentkit) is consumed by downstream repos via a pinned git tag in CI, complete every step of the delivery path before claiming done: source change → commit → push → new git tag → update consumer CI workflow pins → CI checks out the new version.

An editable install (`pip install -e`) makes local tests pass against the source tree, but consumers' CI checks out a pinned git tag, not the local tree. Local tests are one step toward done, not the final verification.

**Before claiming done on a shared-library change:**
1. Check every consumer's CI workflow for how it pins the library (git tag, commit hash, branch).
2. If pinned to a tag, commit and push the library, create a new tag, and update every consumer's workflow to reference it.
3. Confirm every consumer's CI will check out the new version.

The user-facing outcome is CI green. Verify there, not only at local tests.

### 13. A pipeline that runs without crashing is not correct — verify the output on real data

Automated features that pass all unit tests can still produce wrong results
when run against real-world inputs. "Didn't crash" is not the bar. "Produced
the right output" is.

**A passing suite against fakes proves compatibility with the fakes, not with
the real system.** The mock is a model of the external system, and the failure
lives in the model's omissions: a fake that accepts anything makes the unit
suite green while the real system rejects the same input. For every integration
seam (API client, converter, parser, exporter, serializer), either the fake
enforces the external contract's invariants (required headers, format rules,
validation checks), or a live integration test against the real system must
exist. A mock that accepts anything is not a test oracle, it is a rubber stamp.

**A new mechanism for an existing operation must be exercised during the
work, not at the next user request.** When a refactor introduces a new way to
do something that already worked (a new converter, a new write path, a new
serialization), coverage of the old path proves nothing about the new one.
Run a real operation through the new mechanism before declaring the change
done. The bug that survives is the one in the path nobody exercised.

After implementing any feature that transforms data, OCRs images, parses text,
or maps between formats, run it on at least one real-world input. Inspect the
output. If any field is wrong — a wrong name, a wrong amount, a wrong
classification — that is a bug. Fix the root cause before committing. Do not
call the feature done because the pipeline "completed successfully." A
successful pipeline with wrong output is a broken pipeline.

Failure to do this creates a cycle: build → "works" → user points out error
→ fix → "works" → user points out next error. Each round erodes trust. The
first round is avoidable: test on real data before claiming done.

This applies especially to:
- OCR-based extraction where the parser's heuristics differ from reality
- Currency conversion where the detected currency code may be wrong
- Name extraction where frequency-based heuristics pick OCR noise over real names
- Classification where keyword lists miss the domain-specific terms in real data

### 14. Environment substitution is a false convenience — never auto-launch a substitute profile, credential, or directory

When a helper detects that a required environment is absent (browser session, login context, data directory), it must NOT silently substitute a different one. The substitute has different state — different cookies, permissions, data — and downstream code will fail in ways that are hard to diagnose because the swap is hidden inside a convenience function.

The two valid responses:

1. **Fail fast** with a message that tells the user what is missing and how to provide it.
2. **Acquire the exact environment**, not a substitute. If the real browser profile is needed, use the real profile. If that means killing the existing browser and restarting it, do that — but never present a temp profile as "good enough."

A "close enough" environment is never close enough. The gap between the substitute and the real environment is always the thing the caller depends on. This applies to browser profiles, working directories, credential contexts, database connections, and any stateful context that a function auto-creates.

**Auto-launch that hides an environment difference is worse than no auto-launch at all.** A clear error message ("start Brave with --remote-debugging-port") preserves the user's mental model. A silent substitution ("I'll just launch a temp profile for you") breaks it, and the resulting failure appears to be a navigation or auth bug rather than a profile problem.

### 15. Past actions are not prescriptions — never let inference from event reports override explicit user specifications

A user statement of what they did ("I took X", "I tried Y", "I did Z") is a fact about the past, not a directive for the future. The protocol going forward is set by the user's explicit specification, not by whatever they happened to do yesterday.

- **Do not derive a recurring pattern from a one-time action.** "Last night I took 3g" does not mean "3g nightly." "I ate eggs for breakfast" does not mean "eggs daily." An event report answers "what happened." Only the user can answer "what should happen going forward."
- **When the user gives an explicit specification afterward, it is binding.** Any inference from the event report that contradicts it is wrong and must be discarded. The specification always wins over the inference.
- **Paraphrase is lossy compression.** "Last night and this morning" preserves a day boundary that "morning and night" collapses. When writing a user's stated quantity, timing, or frequency to any file, verify: is this exactly what they said, or is it my reworded version? Only the user's exact units are safe.
- **Detection signal: internal contradiction.** If a memory entry's written quantity conflicts with the supporting facts in the same entry (e.g., "6g/day" next to "~28 days at 3g/day"), an inference has silently replaced the specification. Do not write until reconciled.

This is a structural instance of rule 11 (abstract from the specific instance): an event report is one data point; a prescription is the user's stated intention. They are different input categories, and treating one as the other silently alters the user's intent.

### 16. Chart annotation placement: measure the rendered geometry, never guess coordinates

When positioning annotation boxes relative to data (for example "to the right of the last data point with a minimum gap"), do not hard-code x offsets from memory. Measure the rendered artists and compute the position:

1. Measure with the FINAL transform. Apply layout first (`plt.tight_layout()`), then `fig.canvas.draw()`. Measuring before layout is wrong: layout resizes the axes, which changes the data width of every text box, so a box measured pre-layout lands off-target.
2. Measure each box with `artist.get_bbox_patch().get_window_extent()` and each reference element (data marker, value label) with `get_window_extent()`. Convert both to data coordinates via `ax.transData.inverted()`.
3. Find the last data point programmatically (`max` over the plotted x positions), never from an assumed axis index. A miscounted index (last month is index 8, not 7) is a common silent bug that places the box directly on a point.
4. Convert a physical gap into data units: `units_per_mm = xlim_span / (axes_width_in * 25.4)`, where `axes_width_in = ax.get_position().width * fig.get_size_inches()[0]` and `xlim_span = ax.get_xlim()[1] - ax.get_xlim()[0]`.
5. To put the box's left edge at `last_data_x + gap_mm * units_per_mm`: with the text anchored at a reference x (e.g. 0), measure the box's left edge `bx0`; then set the anchor to `desired_left - bx0`. This is exact because the box moves rigidly with its anchor. Equivalently, for a centered box, `anchor = last_data_x + box_width/2 + gap`.
6. After placing, re-measure with the same final transform and verify the box right edge stays inside `xlim` and the gap to the data meets the required minimum.

### 17. Notes must bind every datum to its referent — an ambiguous note is a write-time defect

Notes written by one agent (memory files, Evernote notes, docs, comments) are
read later by an agent that cannot ask the author what was meant. Anything the
author knows but the text does not carry is already lost. The reader's job is
to attach each datum to a subject; if two attachments are possible, the wrong
one will eventually be chosen.

- **Bind every datum to its subject within its own clause.** A number,
  prescription, status, or plan must name what it applies to in the same
  sentence. A sentence whose antecedent could attach to either the preceding
  or the following topic is a defective note. Rewrite it with the subject
  named. The metric is irrelevant: loads, doses, prices, dates, and
  frequencies all misattach the same way when unbound.
- **Plans carry scope: activity, metric, time.** "Load at 50-60% of normal"
  is defective. "Freestyle-return program (swim sessions after 2026-08-18,
  not gym lat work): load at 50-60% of normal volume" survives. An event
  record describes what happened; a plan describes what will be done; a
  dated entry that contains a plan must state the plan's future scope, never
  leave the entry date to imply it.
- **Read side.** When reading a note one did not write, an ambiguity is a
  defect to surface, not a guess to make. Ask the user which reading is
  correct before using the datum.

The write-time test: if a careful reader could attach the datum to the wrong
subject, the note is wrong no matter what the author knows.

### 18. Itinerary rows are exact for mid-stay dates; travel days must be asked

A shared schedule — Chaehan's `memory/travelitinerary.csv` — is
authoritative for where he is on any date inside a stay. Use it exactly
there. On travel days, the last day of one stay or the first day of the
next, the schedule cannot place him: he moves later in the day, plans
shift, and the file can lag reality. On those dates, ASK Chaehan or take
his reported location; his report overrides the file. Never write a city
for a travel day into a note, summary, or message without his
confirmation. When a task involves location, time, travel, or
adaptation-to-place, read the itinerary first; only skip it when the
task is genuinely location-independent.

The principle: when a data source is authoritative for interior values
but ambiguous at boundary values, do not extrapolate the boundary — take
it from the owner. The extrapolated boundary silently corrupts every
record that names it.

Failure: on 2026-08-22, gym sessions were recorded as Budapest (08-20)
and Munich (08-22) straight from the CSV; both were travel days, and the
actual locations were Bucharest and Budapest.

City labels inside other memory or event records (gym logs, episode
notes, quotes) are not location ground truth. Before using a record's
city label in an answer or a write, validate it against the itinerary:
for mid-stay dates the itinerary wins, the conflict is flagged in the
answer, and the record's label is corrected. Failure: on 2026-08-24 a
gym log labeled "Bucharest hotel" for 08-20 was adopted as ground truth
for two answers while the itinerary (08-19 Budapest, 08-22 Munich)
already placed Chaehan in Budapest on 08-20; he corrected: "you could
have derived that from the travel itinerary."

### 19. Notes and summaries: answer first, human words, no hedging rituals

Any text written for the user to read later (decision notes, session
summaries, memory entries, Evernote notes, reports) follows the reader's
order and the reader's language, not the analyst's process.

- **Answer first.** If the document exists to answer a question, the answer
  is the first sentence. Reasoning follows. Never build suspense by saving
  the recommendation for the end.
- **No confidence rituals.** Do not attach labels like "Confidence:
  moderate" or "high confidence on X". State the call. If genuinely
  uncertain, name the specific fact that would change it.
- **Write the sentence a friend would say.** "You risk more hurting the
  shoulder than gaining strength", not "the risk is the serious one and the
  payoff is fictional". Compare concrete outcomes in plain words. Mechanism
  stays; analyst jargon goes. "Benign", "sub-clinical", "protocol signal",
  "fictional payoff", "eliminated by error analysis" are all defects in
  user-facing prose.
- **One claim per sentence.** Short sentences, no semicolon chains, no em
  dashes (rule 2).
- **Cut restatement, keep numbers.** Each fact appears once, in the place
  where it does the most work. Concrete numbers, dates, names, and places
  survive every cut. Repeated descriptions of the same option do not.

Detection signal: if a note reads like the transcript of an analysis
(reframe, enumeration, assumptions, reveal), it is in the wrong order. The
reader's questions are: what do I do, why, what would change it. In that
order.

### 20. The date goes at the beginning of the title, never in the body

A note about a dated decision, event, or session carries its date at the
start of the title, not as a line in the body. The title is the first thing
a reader scans; it must tell them when. A "Date:" line in the body is a
defect.

- Evernote note titles: `2026-08-21 Decision: Lats session scheduling
  Budapest`, not `Decision: Lats session scheduling Budapest` with a
  `Date: 2026-08-21` line inside.
- Local decision files: the date already leads the filename
  (`decisions/YYYY-MM-DD-slug.md`); do not duplicate it as a body line.
- If the date is unknown, leave it out of the title rather than inventing
  one from context.

### 21. A focused question gets a two-sentence answer

A focused question (what day, what cause, yes/no, what to do) gets two
plain sentences: the conclusion with the decisive number, then what
follows from it. Mechanism blocks, venue tables, and caveat stacks come
only when the user asks for depth. The user's model answer:

"For the cold, the Friday night cold can be ruled out as cause as it
needs median 1.9 d for incubation. This makes much more likely the
late-night 08-19 Bucharest→Budapest flight."

Failure: on 2026-08-24 a cause/date query got a five-section answer with
mechanism blocks, a candidate table, and caveats; Chaehan rejected it as
"incredibly overcomplicated" and supplied the two-sentence format as the
standard.

### 22. User-stated patterns are facts, not bias observations

When the user states a recurring pattern as a plain causal claim ("this
is the second time cold exposure triggered a cold"), record it verbatim
in the domain memory file as a fact. Do not relabel it as a cognitive
bias ("salience-driven attribution") — that converts his stated view
into a judgment error. A psychological observation is written only when
the user endorses the psychological reading himself. An agent-invented
bias hypothesis the user rejects is removed from the psych-observations
file entirely, not defended or marked superseded — his "don't record"
overrides any never-delete guideline.

Failure: on 2026-08-24 a "salience" psych observation was
batch-confirmed, then rejected ("salience is a wrong hypothesis"); the
user's actual point was the plain recurrence fact, which belongs in the
health memory file.

### 23. "General agent instructions" always means agentkit

When Chaehan refers to "the general agent instructions" or "the overall
agent instructions" without naming a project-specific workflow, the
target is agentkit: RULES.md (this file) is the canonical home for
behavioral rules. Project repos carry only project-specific workflows in
their `.opencode/agents/` files; global behavior rules are referenced
there as pointers, never defined or duplicated. AGENTS.md delegates rule
text to RULES.md, so new rules go into RULES.md, not AGENTS.md.

Failure: on 2026-08-24 an instruction to "change the overall agent
instructions" (two-sentence answer format, pattern-as-fact rule) was
implemented in a project repo (.opencode/agents/socrates.md); Chaehan
corrected: "you still confuse where to put the overall agent
instructions: it is always in agentkit!"

### 24. User-designated plan hierarchy is binding

When the user marks one option as the main plan and another as an
alternative or fallback, that hierarchy is part of the specification.
Present the main plan as the plan and the alternative as conditional on
its trigger (e.g., "if twice-a-day training proves unsustainable"). Do
not promote the fallback to the main presentation, and do not drop the
trigger condition when restating the alternative. The failure class:
the agent swapped them and presented the fallback as the main week.

Failure: on 2026-08-24 swim routine planning, the user proposed "second
band on Thu and Sat aerobic as alternative" to the main course of
Wed-interval-plus-band double days; the agent presented Mon+Thu band as
the main week. User: "the band on Thu is an alternative, not the main
course which is Wed interval + band!"

### 25. Protocol schemes must match the stated training goal

When proposing a training or dosing scheme, anchor every parameter
(reps, sets, load, frequency, progression rule) to the goal the user
stated. A generic default that serves a different goal is an error even
if the scheme is internally sound for that other goal. Before
presenting any scheme, name the adaptation it targets (max force,
muscle size, endurance, skill) and check each parameter against it. If
the available tool limits the goal (e.g., a resistance band underloads
most of the range for max strength), state the limitation instead of
silently adapting the scheme away from the goal.

Failure: on 2026-08-24 the agent proposed a hypertrophy double
progression (work up to 15 reps, then increase band thickness) for lats
training whose stated goal was max strength acquisition. User: "this is
not good for max strength acquisition!" The goal-matched scheme: 3-6
reps at high tension, 2-3 min rest, progress by adding resistance only,
never by extending reps beyond the strength range.

## Shell: `~/.bash_aliases` (user-global)

For anything that should persist across shells:
- Add aliases to `~/.bash_aliases` (or `~/.zshrc` for zsh — bash is used).
- **Do not** suggest `~/.bashrc` as the only/default location.
- macOS login shells load `~/.bash_profile`, not `~/.bashrc`.
- For Python envs: follow the repo README — don't assume `python -m venv` when the repo documents **mamba** + `environment.yml`.
