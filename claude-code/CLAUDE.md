# agentkit, for Claude Code

`~/.claude/CLAUDE.md` links here. Claude Code reads CLAUDE.md files only, so
this file and every project's CLAUDE.md are import stubs for the opencode
files. The instructions themselves live in those files.

@~/Software/Prototypes/agentkit/AGENTS.md

## Claude Code specifics

- `RULES.md` is not imported. Read `rules.index.md`, then the line range the
  task needs, exactly as AGENTS.md says for opencode.
- Every change to agent behaviour goes into an opencode file, never into a
  CLAUDE.md (RULES.md rule 257): a rule for every agent into `RULES.md`, a core
  step into `AGENTS.md`, one project's workflow into its
  `.opencode/agents/<name>.md` or `AGENTS.md`, a procedure into
  `agentkit/skills/<name>/SKILL.md`, a trigger into `agentkit/commands/<name>.md`.
- Agent files keep opencode's frontmatter (`description`, `mode`, `model`,
  `permission`); Claude Code's subagent fields (`name`, `tools`) do not belong
  there. Find them all with
  `ls ~/Software/Prototypes/*/.opencode/agents/*.md ~/.config/opencode/agents/*.md`.
- Never create `~/.claude/agents/` or `~/.claude/rules/`, and never write
  Claude Code's own auto-memory. Memory is the project's `memory/` folder.
- These paths are symlinks; edit the source in agentkit, never the link:
  `~/.claude/CLAUDE.md` (this file), `~/.claude/skills` (→ `~/.agents/skills`),
  `~/.claude/commands` and `~/.config/opencode/commands` (→ `agentkit/commands`),
  `~/.config/opencode/AGENTS.md` and `agents/agentkit.md` (→ `AGENTS.md`).
- `scripts/link_claude_code.sh` recreates the links and the project stubs on a
  new machine, idempotently.
