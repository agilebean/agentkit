# Implementation Plan: Claude Code integration with agentkit

**Goal**: Both Claude Code and opencode read the same canonical behavioral rules from one file. Each tool gets its own path conventions from its own entry point. No duplicated rules. No "read X as Y" remapping. No "ignore this section" filtering. A new repo needs zero configuration to inherit the rules under either tool.

## Architecture

```
agentkit/RULES.md          (NEW — tool-agnostic behavioral rules, single source of truth)
agentkit/AGENTS.md          (REWRITTEN — opencode-specific conventions only)
~/.config/opencode/opencode.jsonc   (MODIFIED — loads RULES.md via instructions field)
~/.claude/CLAUDE.md         (MODIFIED — loads RULES.md via @ import + Claude conventions)
agentkit/CLAUDE.md          (MODIFIED — loads AGENTS.md via @ import for in-repo work)
~/.claude/skills/<3 names>  (NEW symlinks — completes skill unification)
```

**How each tool loads the rules:**
- opencode: `opencode.jsonc` has `"instructions": ["/Users/chaehan/Software/Prototypes/agentkit/RULES.md"]`. opencode combines instruction files with AGENTS.md. Both load globally for every session, every agent, every repo.
- Claude Code: `~/.claude/CLAUDE.md` has `@/Users/chaehan/Software/Prototypes/agentkit/RULES.md`. Claude Code expands `@` imports at launch. Loads globally for every session, every repo.

**Why this is optimal for weaker models (DeepSeek V4 Pro/Flash):**
- Each tool's context contains only: behavioral rules + that tool's own path conventions. No foreign paths to filter out. No abstraction layer to misinterpret. The model sees exactly what it needs.
- The `@` import and `instructions` mechanisms are tool-level features, expanded before the model sees text. Model capability does not affect whether imports work.

## Verified facts (do not re-check)

1. opencode does NOT support `@path` imports in AGENTS.md text. Source: https://opencode.ai/docs/rules ("While opencode doesn't automatically parse file references in AGENTS.md...")
2. opencode's `instructions` field in `opencode.json` loads external files globally. Supports absolute paths starting with `/` or `~`. Source: https://opencode.ai/docs/config ("File paths can be: Relative to the config file directory, Or absolute paths starting with `/` or `~`")
3. Claude Code supports `@path` imports in CLAUDE.md. Absolute paths work. Max 4 recursive hops. Source: https://docs.claude.com/en/docs/claude-code/memory
4. Claude Code strips HTML comments `<!-- ... -->` before injecting CLAUDE.md content. The memory blocks in existing files are inert.
5. Claude Code loads `@` imports first, then appends the rest of CLAUDE.md. Source: docs say "Claude loads the imported file at session start, then appends the rest."
6. Skills are unified: opencode discovers from `~/.agents/skills/*/SKILL.md` and `~/.claude/skills/*/SKILL.md`. Claude Code discovers from `~/.claude/skills/*/SKILL.md`. Current `~/.claude/skills/<name>` symlinks point to `~/.agents/skills/<name>`, which point to `agentkit/skills/<name>`. Three skills missing Claude symlinks: `evernote`, `grill-instruct`, `sourcing`.
7. `~/.config/opencode/AGENTS.md` and `~/.config/opencode/agents/agentkit.md` are symlinks to `agentkit/AGENTS.md`. Both must remain symlinks. Never Write or Edit the symlink targets.
8. Current AGENTS.md lines 238-242 are an exact duplicate of lines 209-214. This is a copy-paste bug. Remove the duplicate during extraction.

## Scope guard

Files touched:
- `agentkit/RULES.md` (NEW)
- `agentkit/AGENTS.md` (REWRITTEN — extract opencode conventions, rules move to RULES.md)
- `~/.config/opencode/opencode.jsonc` (add instructions field)
- `~/.claude/CLAUDE.md` (add @ import + Claude conventions)
- `agentkit/CLAUDE.md` (add @ import)
- 3 skill symlinks under `~/.claude/skills/`

No `.py` file is edited. Rule 6 (run full pytest after any `.py` edit) does not apply. Do NOT run pytest.

Standing constraint from AGENTS.md Rule 1: never Write or Edit symlinked paths under `~/.config/opencode/`. Always edit the source file `agentkit/AGENTS.md` directly.

## Step 0. Pre-flight checks

Run each command. If any output differs from the expected value, STOP and report. Do not improvise.

0.1 Confirm symlinks point to source:
```
readlink ~/.config/opencode/AGENTS.md && readlink ~/.config/opencode/agents/agentkit.md
```
Both must print `/Users/chaehan/Software/Prototypes/agentkit/AGENTS.md`.

0.2 Confirm `~/.claude/CLAUDE.md` is a real file:
```
ls -la ~/.claude/CLAUDE.md
```
Expected: regular file, not a symlink. Contains `<!-- MEMORY:START -->` block.

0.3 Confirm 3 skills missing Claude symlinks:
```
for s in evernote grill-instruct sourcing; do test -e ~/.claude/skills/$s && echo "$s: present" || echo "$s: MISSING"; done
```
Expected: all three print `MISSING`.

0.4 Confirm `agentkit/CLAUDE.md` is a real file with memory stub.

0.5 Read `~/.config/opencode/opencode.jsonc` and confirm it has no `instructions` field yet.

## Step 1. Create `agentkit/RULES.md` — the canonical tool-agnostic rules

This file contains ALL behavioral rules. No identity line. No tool-specific paths. No tool name references.

1.1 Read `/Users/chaehan/Software/Prototypes/agentkit/AGENTS.md` in full (250 lines).

1.2 Create `/Users/chaehan/Software/Prototypes/agentkit/RULES.md` with the following content. Build it by extracting and modifying sections from the current AGENTS.md:

**Header (replace the current "# General" + identity line + "## Agent Rules" with):**
```
# Agent Rules

The rules in this section are **non-waivable**. A project-specific workflow or
local rules file may add steps, constrain scope, or prescribe a sequence, but it
cannot remove, skip, or soften any obligation below. Specifically: any edit to a
``.py`` file, for any reason, including inside a local workflow, triggers the
full test suite requirement in rule 6. No local instruction can waive this.
```

Note two changes from the original:
- Removed "You are opencode..." identity line (each tool's entry point provides identity).
- Changed "local AGENTS.md" to "local rules file" (tool-agnostic).
- Changed "rule 5" to "rule 6" (the test suite requirement is rule 6, not rule 5 — this fixes a pre-existing numbering error).

**Rule 1 — abstract the principle (replace the opencode-specific version):**
```
### 1. NEVER write to symlinked config paths — always edit the source file

Configuration files under tool-specific directories may be symlinks pointing
back to source repos. Replacing a symlink with a real file destroys the backup
connection. Always edit the source file in the repository, never the symlink
target. Tool-specific symlink paths are documented in each tool's convention
file.
```

**Rules 2 through 13 + all intermediate sections:** Copy verbatim from current AGENTS.md lines 43 through 250, with these modifications:
- Line 97: change "The AGENTS.md or README may say" to "The project rules file or README may say"
- Lines 238-242: DELETE these lines. They are an exact duplicate of lines 209-214 (Rule 12's numbered steps appear twice). Keep only the first occurrence (lines 209-214).
- No other changes to the text of rules 2-13, causal reasoning, TDD, concise confirmations, invariants, extraction, shell sections.

1.3 Read the completed `RULES.md` and verify:
- First line is `# Agent Rules` (no identity line, no "# General")
- Rule 1 contains no path references to `~/.config/opencode/` or `~/.claude/`
- No occurrence of the word "opencode" anywhere in the file
- No occurrence of the duplicate block (Rule 12's numbered steps appear exactly once)
- Rules 2-13 are present and unchanged from the original

## Step 2. Rewrite `agentkit/AGENTS.md` — opencode-specific conventions only

This file keeps the opencode identity, the opencode-specific path conventions, and the agentkit architecture section. All behavioral rules are now in RULES.md.

2.1 Overwrite `/Users/chaehan/Software/Prototypes/agentkit/AGENTS.md` with this exact content:

```
# General

You are opencode, an interactive CLI tool that helps users with software engineering tasks.

## opencode path conventions

The following paths are symlinks to source files in the agentkit repository. Never use Write or Edit tools on these symlinked paths. Always edit the source file directly.

- `~/.config/opencode/AGENTS.md` → `/Users/chaehan/Software/Prototypes/agentkit/AGENTS.md` (this file — global rules entry point)
- `~/.config/opencode/agents/agentkit.md` → `/Users/chaehan/Software/Prototypes/agentkit/AGENTS.md` (agent definition)
- `~/.agents/skills/<name>/` → `/Users/chaehan/Software/Prototypes/agentkit/skills/<name>/` (skill definitions)

Project-specific `.opencode/agents/*.md` files in individual repos are NOT symlinked and are safe to edit.

## agentkit architecture

`agentkit/skills/` contains cross-project skill definitions. To make a skill available to all agents, symlink it into `~/.agents/skills/`:

```
ln -sfn ~/Software/Prototypes/agentkit/skills/<name> ~/.agents/skills/<name>
```

opencode auto-loads `**/SKILL.md` from `~/.agents/skills/`. Once symlinked, the skill appears in the `available_skills` list for every agent.

Agent definitions in `.opencode/agents/` are project-specific. Cross-project agent behaviors go in agentkit and are loaded via global rules. Skills go in `agentkit/skills/`.

## Behavioral rules

Behavioral rules are loaded globally via the `instructions` field in `opencode.jsonc`. See `agentkit/RULES.md` for the canonical rule text. Do not duplicate rules here.
```

2.2 Read the completed `AGENTS.md` and verify:
- Contains the opencode identity line
- Contains opencode path conventions with specific `~/.config/opencode/` paths
- Contains the agentkit architecture section with the `ln -sfn` command
- Does NOT contain rules 2-13, causal reasoning, TDD, concise confirmations, invariants, or shell sections
- Contains the reference to RULES.md at the bottom

## Step 3. Add RULES.md to opencode's `instructions` field

3.1 Read `~/.config/opencode/opencode.jsonc`.

3.2 Add the `instructions` field. The final file must look like:
```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "permission": "allow",
  "instructions": ["/Users/chaehan/Software/Prototypes/agentkit/RULES.md"],
  "mcp": {
    "evernote": {
      "type": "remote",
      "url": "https://mcp.evernote.com/mcp"
    }
  }
}
```

Use the absolute path. Do not use `~` — the `instructions` field path resolution for absolute paths is confirmed for `/`-prefixed paths in the config docs. If the smoke test in Step 7 shows rules not loading, try `~/Software/Prototypes/agentkit/RULES.md` as a fallback.

3.3 Read the file back and confirm the `instructions` array contains the RULES.md path.

## Step 4. Wire `~/.claude/CLAUDE.md` — import RULES.md + Claude conventions

4.1 Read `~/.claude/CLAUDE.md` in full. Preserve the `<!-- MEMORY:START --> ... <!-- MEMORY:END -->` block verbatim.

4.2 Overwrite the file with this exact content:
```
<!-- MEMORY:START -->
# .claude

_Last updated: 2026-05-02 | 0 active memories, 0 total_

_For deeper context, use memory_search, memory_related, or memory_ask tools._
<!-- MEMORY:END -->

@/Users/chaehan/Software/Prototypes/agentkit/RULES.md

## Claude Code path conventions

The following paths are symlinks to source files. Never use Write or Edit tools on these symlinked paths. Always edit the source file in the repository.

- `~/.claude/skills/<name>/` → `~/.agents/skills/<name>/` → `/Users/chaehan/Software/Prototypes/agentkit/skills/<name>/` (skill definitions)

`~/.claude/CLAUDE.md` is a real file, not a symlink. Edit it directly.

To add a new skill available to both Claude Code and opencode:
```
ln -sfn ~/Software/Prototypes/agentkit/skills/<name> ~/.agents/skills/<name>
ln -sfn ~/.agents/skills/<name> ~/.claude/skills/<name>
```
```

The `@RULES.md` import is expanded first by Claude Code, then the rest of the file is appended. Context order: rules, then Claude conventions. This is the correct order — rules are primary, conventions are supplementary reference.

4.3 Read the file back and confirm: memory block preserved, `@` import line present with absolute path, Claude conventions section present.

## Step 5. Wire `agentkit/CLAUDE.md` — import AGENTS.md for in-repo work

When Claude Code runs inside the agentkit repo, it loads both `~/.claude/CLAUDE.md` (user-level, imports RULES.md) and `agentkit/CLAUDE.md` (project-level). The project-level file should import `@AGENTS.md` so Claude sees opencode path conventions when working on agentkit itself. Do NOT import RULES.md here — it is already loaded from user-level `~/.claude/CLAUDE.md`. Double-loading wastes context tokens.

5.1 Read `/Users/chaehan/Software/Prototypes/agentkit/CLAUDE.md`.

5.2 Overwrite with this exact content:
```
<!-- MEMORY:START -->
# agentkit

_Last updated: 2026-05-25 | 0 active memories, 0 total_

_For deeper context, use memory_search, memory_related, or memory_ask tools._
<!-- MEMORY:END -->

@AGENTS.md
```

The `@AGENTS.md` import uses a relative path. It resolves relative to `agentkit/CLAUDE.md`, so it finds `agentkit/AGENTS.md`. This gives Claude the opencode path conventions and architecture section when working in the agentkit repo.

5.3 Read the file back and confirm: memory block preserved, `@AGENTS.md` import present.

## Step 6. Add the 3 missing Claude skill symlinks

6.1 Run these three commands:
```
ln -sfn ~/Software/Prototypes/agentkit/skills/evernote ~/.claude/skills/evernote
ln -sfn ~/Software/Prototypes/agentkit/skills/grill-instruct ~/.claude/skills/grill-instruct
ln -sfn ~/Software/Prototypes/agentkit/skills/sourcing ~/.claude/skills/sourcing
```

6.2 Verify all three resolve to the source:
```
for s in evernote grill-instruct sourcing; do readlink -f ~/.claude/skills/$s; done
```
Each must print a path ending in `agentkit/skills/<name>`. If any prints a path containing `..` or does not resolve, redo Step 6.1 with absolute source paths: `ln -sfn /Users/chaehan/Software/Prototypes/agentkit/skills/<name> ~/.claude/skills/<name>`.

## Step 7. Verification (do not skip any check)

7.1 Confirm RULES.md has no tool-specific content:
```
rg -i "opencode|~/.config/opencode|~/.claude" /Users/chaehan/Software/Prototypes/agentkit/RULES.md
```
Expected: no matches. If any match, RULES.md contains tool-specific paths that must be moved to AGENTS.md or CLAUDE.md.

7.2 Confirm RULES.md has all 13 numbered rules:
```
rg "^### [0-9]+\." /Users/chaehan/Software/Prototypes/agentkit/RULES.md
```
Expected: 13 matches (rules 1 through 13).

7.3 Confirm RULES.md has no duplicate Rule 12 block:
```
rg -c "Check every consumer's CI workflow" /Users/chaehan/Software/Prototypes/agentkit/RULES.md
```
Expected: `1`. If `2`, the duplicate was not removed.

7.4 Confirm AGENTS.md has opencode conventions but no behavioral rules:
```
rg "^### [0-9]+\." /Users/chaehan/Software/Prototypes/agentkit/AGENTS.md
```
Expected: no matches (numbered rules are in RULES.md now).

7.5 Confirm AGENTS.md still has the identity line and path conventions:
```
rg "You are opencode|~/.config/opencode" /Users/chaehan/Software/Prototypes/agentkit/AGENTS.md
```
Expected: matches for both.

7.6 Confirm opencode.jsonc has the instructions field:
```
rg "RULES.md" ~/.config/opencode/opencode.jsonc
```
Expected: one match.

7.7 Confirm ~/.claude/CLAUDE.md has the @ import:
```
rg "@.*RULES" ~/.claude/CLAUDE.md
```
Expected: one match.

7.8 Confirm agentkit/CLAUDE.md has the @ import:
```
rg "@AGENTS" /Users/chaehan/Software/Prototypes/agentkit/CLAUDE.md
```
Expected: one match.

7.9 Confirm skill symlinks are unified:
```
diff <(ls ~/.claude/skills/) <(ls ~/.agents/skills/) && echo IDENTICAL
```
Expected: `IDENTICAL`.

7.10 Live smoke test — opencode: Launch an opencode session. Ask it: "List the non-waivable agent rules." It must recite rules from RULES.md (loaded via `instructions`). If it cannot recite the rules, the `instructions` path did not resolve. Try the fallback path with `~` prefix. If still failing, check opencode debug output: `opencode debug config` and look for the instructions field.

7.11 Live smoke test — Claude Code: Open a Claude Code session in any directory. Run `/memory`. The listed files must include `~/.claude/CLAUDE.md` with the RULES.md import resolved. If the import is not listed, the absolute path is wrong or the file does not exist at that path. Check with `ls -la /Users/chaehan/Software/Prototypes/agentkit/RULES.md`.

7.12 Live smoke test — Claude Code in agentkit repo: Open a Claude Code session inside `/Users/chaehan/Software/Prototypes/agentkit/`. Run `/memory`. The listed files must include both `~/.claude/CLAUDE.md` (with RULES.md) and `agentkit/CLAUDE.md` (with AGENTS.md). Confirm no double-loading of RULES.md.

## Step 8. Onboarding recipe for future repos (documentation only)

No per-repo configuration is needed to inherit agentkit rules. Both tools load RULES.md globally:
- opencode: via `instructions` in `~/.config/opencode/opencode.jsonc`
- Claude Code: via `@` import in `~/.claude/CLAUDE.md`

If a repo needs project-specific rules on top of the global ones:
- opencode: add a project-level `AGENTS.md` in the repo root
- Claude Code: add a project-level `CLAUDE.md` in the repo root (or `.claude/CLAUDE.md`)

These layer on top of the global rules. They do not replace them.

## Acceptance criteria (all must be true)

- [ ] `agentkit/RULES.md` exists and contains all 13 numbered rules + causal reasoning + TDD + concise confirmations + invariants + shell sections.
- [ ] `rg -i "opencode" agentkit/RULES.md` returns no matches.
- [ ] `agentkit/AGENTS.md` contains only opencode identity + path conventions + architecture section + reference to RULES.md. No numbered behavioral rules.
- [ ] `~/.config/opencode/opencode.jsonc` has `"instructions": ["/Users/chaehan/Software/Prototypes/agentkit/RULES.md"]`.
- [ ] `~/.claude/CLAUDE.md` has `@/Users/chaehan/Software/Prototypes/agentkit/RULES.md` import + Claude path conventions. Memory block preserved.
- [ ] `agentkit/CLAUDE.md` has `@AGENTS.md` import. Memory block preserved. No RULES.md import (avoids double-load).
- [ ] `diff <(ls ~/.claude/skills/) <(ls ~/.agents/skills/)` prints `IDENTICAL`.
- [ ] opencode session recites rules from RULES.md.
- [ ] Claude Code `/memory` shows RULES.md import resolved.
- [ ] No `.py` file was edited.
