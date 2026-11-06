#!/usr/bin/env bash
# Link agentkit into Claude Code and opencode, and write each project's
# CLAUDE.md import stub. Everything is a symlink to agentkit or a stub of `@`
# imports, so the opencode files stay the only source (RULES.md rule 257).
# Idempotent. Override locations with AGENTKIT=, AGENTS_HOME=, CLAUDE_HOME=,
# OPENCODE_HOME=, PROJECTS=.
set -euo pipefail

AGENTKIT="${AGENTKIT:-$HOME/Software/Prototypes/agentkit}"
AGENTS_HOME="${AGENTS_HOME:-$HOME/.agents}"
CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
OPENCODE_HOME="${OPENCODE_HOME:-$HOME/.config/opencode}"
PROJECTS="${PROJECTS:-$(dirname "$AGENTKIT")}"
STUB='<!-- import stub: instructions live in the opencode files below (agentkit RULES.md rule 257) -->'

[ -f "$AGENTKIT/AGENTS.md" ] || { echo "no agentkit at $AGENTKIT" >&2; exit 1; }

# Replace a directory that holds only symlinks by one link to $1.
link_dir() {
  local target="$1" link="$2"
  if [ -d "$link" ] && [ ! -L "$link" ]; then
    if find "$link" -mindepth 1 -maxdepth 1 ! -type l | grep -q .; then
      echo "skip $link: holds real files" >&2; return
    fi
    rm -rf "$link"
  fi
  ln -sfn "$target" "$link"
}

mkdir -p "$AGENTS_HOME/skills" "$CLAUDE_HOME" "$OPENCODE_HOME/agents"

# agentkit skills join the third-party skills in ~/.agents/skills (opencode);
# Claude Code sees the whole directory through one link.
for dir in "$AGENTKIT"/skills/*/; do
  ln -sfn "${dir%/}" "$AGENTS_HOME/skills/$(basename "$dir")"
done
link_dir "$AGENTS_HOME/skills" "$CLAUDE_HOME/skills"
link_dir "$AGENTKIT/commands" "$CLAUDE_HOME/commands"
link_dir "$AGENTKIT/commands" "$OPENCODE_HOME/commands"

ln -sfn "$AGENTKIT/claude-code/CLAUDE.md" "$CLAUDE_HOME/CLAUDE.md"
ln -sfn "$AGENTKIT/AGENTS.md" "$OPENCODE_HOME/AGENTS.md"
ln -sfn "$AGENTKIT/AGENTS.md" "$OPENCODE_HOME/agents/agentkit.md"

# Project stubs: AGENTS.md and the agent named after the repo. agentkit itself
# needs none, since ~/.claude/CLAUDE.md already imports its AGENTS.md. A
# CLAUDE.md without the stub marker is someone's own file and is left alone.
for repo in "$PROJECTS"/*/; do
  repo="${repo%/}"; name="$(basename "$repo")"
  [ "$repo" = "$AGENTKIT" ] && continue
  imports=""
  [ -f "$repo/AGENTS.md" ] && imports+="@AGENTS.md"$'\n'
  [ -f "$repo/.opencode/agents/$name.md" ] && imports+="@.opencode/agents/$name.md"$'\n'
  [ -n "$imports" ] || continue
  if [ -f "$repo/CLAUDE.md" ] && ! head -1 "$repo/CLAUDE.md" | grep -qF "$STUB"; then
    echo "skip $repo/CLAUDE.md: not a stub" >&2; continue
  fi
  printf '%s\n%s' "$STUB" "$imports" > "$repo/CLAUDE.md"
  echo "stub:     $repo/CLAUDE.md"
done

echo "claude:   $CLAUDE_HOME/CLAUDE.md -> $(readlink "$CLAUDE_HOME/CLAUDE.md")"
echo "skills:   $(ls "$CLAUDE_HOME/skills/" | wc -l | tr -d ' ') via $CLAUDE_HOME/skills"
echo "commands: $(ls "$CLAUDE_HOME/commands/" | wc -l | tr -d ' ') via $CLAUDE_HOME/commands"
