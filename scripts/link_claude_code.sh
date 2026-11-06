#!/usr/bin/env bash
# Link agentkit into Claude Code and opencode.
#
# Everything it creates is a symlink to a file in this repository, so a new
# machine needs only: clone agentkit, run this script. Nothing is copied, so
# the repository stays the single source of truth.
#
# Idempotent: running it again re-points the same links and creates nothing new.
#
# Override locations with AGENTKIT=, AGENTS_HOME=, CLAUDE_HOME=, OPENCODE_HOME=.
set -euo pipefail

AGENTKIT="${AGENTKIT:-$HOME/Software/Prototypes/agentkit}"
AGENTS_HOME="${AGENTS_HOME:-$HOME/.agents}"
CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
OPENCODE_HOME="${OPENCODE_HOME:-$HOME/.config/opencode}"

[ -f "$AGENTKIT/AGENTS.md" ] || { echo "no agentkit at $AGENTKIT" >&2; exit 1; }

mkdir -p "$AGENTS_HOME/skills" "$CLAUDE_HOME/skills" "$CLAUDE_HOME/commands" \
         "$OPENCODE_HOME/agents" "$OPENCODE_HOME/commands"

# User-scope Claude Code memory file: one symlink, whole rule set.
ln -sfn "$AGENTKIT/claude-code/CLAUDE.md" "$CLAUDE_HOME/CLAUDE.md"

# Skills: agentkit -> ~/.agents/skills (opencode) -> ~/.claude/skills (Claude Code)
for dir in "$AGENTKIT"/skills/*/; do
  name="$(basename "$dir")"
  ln -sfn "$AGENTKIT/skills/$name" "$AGENTS_HOME/skills/$name"
  ln -sfn "$AGENTS_HOME/skills/$name" "$CLAUDE_HOME/skills/$name"
done

# Slash commands
for file in "$AGENTKIT"/commands/*.md; do
  name="$(basename "$file")"
  ln -sfn "$file" "$CLAUDE_HOME/commands/$name"
  ln -sfn "$file" "$OPENCODE_HOME/commands/$name"
done

# opencode instruction files
ln -sfn "$AGENTKIT/AGENTS.md" "$OPENCODE_HOME/AGENTS.md"
ln -sfn "$AGENTKIT/AGENTS.md" "$OPENCODE_HOME/agents/agentkit.md"

printf '%s\n' "claude:   $CLAUDE_HOME/CLAUDE.md"
printf '%s\n' "skills:   $(find "$CLAUDE_HOME/skills" -maxdepth 1 -type l | wc -l | tr -d ' ') linked"
printf '%s\n' "commands: $(find "$CLAUDE_HOME/commands" -maxdepth 1 -type l | wc -l | tr -d ' ') linked"
