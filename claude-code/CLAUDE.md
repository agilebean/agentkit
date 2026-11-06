<!-- MEMORY:START -->
# .claude

_Last updated: 2026-11-06 | 0 active memories, 0 total_

_For deeper context, use memory_search, memory_related, or memory_ask tools._
<!-- MEMORY:END -->

# agentkit, for Claude Code

`~/.claude/CLAUDE.md` is a symlink to this file, so this content lives in git and
travels with the repository. Edit it here, never through the link.

@~/Software/Prototypes/agentkit/AGENTS.md
@~/Software/Prototypes/agentkit/RULES.md

## Claude Code path conventions

The following paths are symlinks to source files. Never use Write or Edit tools on these symlinked paths. Always edit the source file in the repository.

- `~/.claude/skills/<name>/` → `~/.agents/skills/<name>/` → `~/Software/Prototypes/agentkit/skills/<name>/` (skill definitions)
- `~/.claude/commands/<name>.md` → `~/Software/Prototypes/agentkit/commands/<name>.md` (slash commands)
- `~/.claude/CLAUDE.md` → `~/Software/Prototypes/agentkit/claude-code/CLAUDE.md` (this file)

`~/Software/Prototypes/agentkit/scripts/link_claude_code.sh` recreates every one of
these links, idempotently. It is the whole setup on a new machine.

## Agent definitions

opencode agent files are the source of truth for agent behavior. Never create a
parallel copy in `~/.claude/agents/`.

- Project agents: `~/Software/Prototypes/<repo>/.opencode/agents/*.md`
- Global agents: `~/.config/opencode/agents/` — `agentkit.md` is a symlink to
  `agentkit/AGENTS.md`; edit that source, not the link
- Discover all: `ls ~/Software/Prototypes/*/.opencode/agents/*.md ~/.config/opencode/agents/*.md`

Frontmatter is opencode's (`description`, `mode`, `model`, `permission`).
Claude Code's subagent fields (`name`, `tools`) do not belong here.

A project's `CLAUDE.md` imports its own agent file, for example
`socrates/CLAUDE.md` has `@.opencode/agents/socrates.md`. That import is relative
and lives in the project's own repository, so it needs no link.
