// note-gate - refuses an Evernote whole-body write through MCP whose text did
// not pass the note gate (agentkit skills/life-overview/scripts/overview_gate.py).
// A weaker model reads a brief or a rule for what it allows; a refusal at the
// write is the one point every path passes (failure 164 in socrates
// memory/agentic_ai.md). The CLI path is refused by the socrates Evernote CLI
// itself (exit 7); this covers the `execute` tool's MCP calls.
//
// A whole-body write is a new note, an append, or an edit that replaces the
// body (its code carries `</en-note>` or runs past 6000 characters). It passes
// when its code carries a `note-gate:<sha>` marker whose stamp file exists and
// is under 3 hours old. Surgical edits (a cell, an image tag) are left alone.

import { Plugin } from "@opencode/plugin"
import { existsSync, statSync } from "node:fs"
import { homedir } from "node:os"
import { join } from "node:path"

const MAX_AGE_MS = 3 * 60 * 60 * 1000

export function stampDir(): string {
  return process.env.NOTE_GATE_STAMPS || join(homedir(), ".local/state/agentkit/note-gate")
}

export function isBodyWrite(code: string): boolean {
  if (/\bevernote\.create_note\s*\(/.test(code)) return true
  if (!/\bevernote\.edit_note\s*\(/.test(code)) return false
  return /<\/en-note>/.test(code) || /mode\s*:\s*["']append["']/.test(code) || code.length > 6000
}

export function hasLiveStamp(code: string, now: number = Date.now()): boolean {
  for (const m of code.matchAll(/note-gate:([0-9a-f]{64})/g)) {
    const f = join(stampDir(), m[1])
    if (existsSync(f) && now - statSync(f).mtimeMs < MAX_AGE_MS) return true
  }
  return false
}

export const MESSAGE =
  "An Evernote note body is written only after the note gate passed it. Build the text with " +
  "~/Software/Prototypes/agentkit/skills/evernote/scripts/note_build.py (evernote skill, section " +
  "\"Writing or rewriting a note's text\"). Its PASS prints a line note-gate:<sha>. Put that line " +
  "into this code as a comment and send the call again."

export default Plugin.define({
  id: "agentkit.note-gate",
  async setup(ctx) {
    await ctx.tool.hook("execute.before", (event) => {
      if (event.tool !== "execute") return
      const code = String((event.input as { code?: string } | undefined)?.code ?? "")
      if (isBodyWrite(code) && !hasLiveStamp(code)) throw new Error(MESSAGE)
    })
  },
})
