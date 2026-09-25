# General

You are opencode, an interactive CLI tool that helps users with software engineering tasks.

## opencode path conventions

The following paths are symlinks to source files in the agentkit repository. Never use Write or Edit tools on these symlinked paths. Always edit the source file directly.

- `~/.config/opencode/AGENTS.md` → `~/Software/Prototypes/agentkit/AGENTS.md` (this file — global rules entry point)
- `~/.config/opencode/agents/agentkit.md` → `~/Software/Prototypes/agentkit/AGENTS.md` (agent definition)
- `~/.agents/skills/<name>/` → `~/Software/Prototypes/agentkit/skills/<name>/` (skill definitions)

Project-specific `.opencode/agents/*.md` files in individual repos are NOT symlinked and are safe to edit.

## agentkit architecture

`agentkit/skills/` contains cross-project skill definitions. To make a skill available to all agents, symlink it into `~/.agents/skills/`:

```
ln -sfn ~/Software/Prototypes/agentkit/skills/<name> ~/.agents/skills/<name>
```

opencode auto-loads `**/SKILL.md` from `~/.agents/skills/`. Once symlinked, the skill appears in the `available_skills` list for every agent.

Agent definitions in `.opencode/agents/` are project-specific. Cross-project agent behaviors go in agentkit and are loaded via global rules. Skills go in `agentkit/skills/`.

## Behavioral rules

**Read `RULES.md` in this folder before you start a task, and treat it as binding.** It is the canonical rule text. At minimum read the section that governs what you are about to do, and follow the pointers to it from the agent definition.

Why this line exists: opencode's `instructions` field does not load this file in v2.0.16. Probe of 2026-09-25 (config carried both `RULES.md` via a config-dir symlink and `$HOME/.../agentkit/RULES.md`): a freshly created session could confirm this file's text and the agent prompt, but not one sentence of RULES.md. A GitHub user who clones agentkit and symlinks this AGENTS.md into `~/.config/opencode/` gets the rules through this pointer, with no absolute path anywhere.

Do not duplicate rule text here.
