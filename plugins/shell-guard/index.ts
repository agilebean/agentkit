import { Plugin } from "@opencode/plugin"

const MAX_TIMEOUT_MS = 60_000

const BLOCKS: Array<{ re: RegExp; invocation?: RegExp; msg: string }> = [
  {
    re: /\bfind\s+["']?(?:~|\$HOME|\/Users|\/)["']?(?:\/|\s|$)/,
    msg:
      "Blocked by agentkit.shell-guard: `find` over home, /Users or /. " +
      "Use `fd` bounded to the project (e.g. `fd -e md . <project>`), or " +
      "`mdfind` for indexed search (RULES 73).",
  },
  {
    re: /\bgrep\b[^\n]*-[a-zA-Z]*[rR][a-zA-Z]*[^\n]*(?:~\/|\$HOME|\/Users|CloudStorage)/,
    msg:
      "Blocked by agentkit.shell-guard: recursive `grep` over home/Google " +
      "Drive. Use `rg` (300x faster on the Drive mount, RULES 73).",
  },
  {
    re: /with timeout of\s+(?:\d{3,})/,
    invocation: /\bosascript\b/,
    msg:
      "Blocked by agentkit.shell-guard: `with timeout of` above 60 s. Cap at " +
      "60 s and run long app automation in the background with a progress log " +
      "(RULES 73).",
  },
]

// Spans of quoted text ('...' and "..."), including the quotes. Quoted text is
// data: it never triggers a block. The exception is the script handed to
// osascript — that payload lives inside quotes, so its rule is anchored on an
// unquoted `osascript` occurrence (a real invocation) instead.
function quotedSpans(cmd: string): Array<[number, number]> {
  const spans: Array<[number, number]> = []
  let i = 0
  while (i < cmd.length) {
    const q = cmd[i]
    if (q !== "'" && q !== '"') {
      i += 1
      continue
    }
    const start = i
    i += 1
    while (i < cmd.length) {
      if (q === '"' && cmd[i] === "\\") {
        i += 2
        continue
      }
      if (cmd[i] === q) {
        i += 1
        break
      }
      i += 1
    }
    spans.push([start, i])
  }
  return spans
}

// True when `re` matches at a position outside every quoted span.
function matchesOutsideQuotes(
  cmd: string,
  spans: Array<[number, number]>,
  re: RegExp,
): boolean {
  const rx = new RegExp(re.source, re.flags.includes("g") ? re.flags : re.flags + "g")
  let m: RegExpExecArray | null
  while ((m = rx.exec(cmd)) !== null) {
    const at = m.index
    if (!spans.some(([s, e]) => at >= s && at < e)) return true
    if (rx.lastIndex === m.index) rx.lastIndex += 1
  }
  return false
}

function deny(event: { command: string }, msg: string): void {
  const quoted = msg.replace(/'/g, `'\\''`)
  event.command = `printf '%s\\n' '${quoted}' >&2; exit 1`
}

export default Plugin.define({
  id: "agentkit.shell-guard",
  async setup(ctx) {
    await ctx.shell.hook("create.before", (event) => {
      // 1) cap explicit long timeouts (0 = "no timeout", leave alone)
      if (typeof event.timeout === "number" && event.timeout > MAX_TIMEOUT_MS) {
        event.timeout = MAX_TIMEOUT_MS
      }
      // 2) deny banned patterns; quoted text is inert (osascript payload aside)
      const cmd = event.command ?? ""
      const spans = quotedSpans(cmd)
      for (const b of BLOCKS) {
        const hit = b.invocation
          ? b.re.test(cmd) && matchesOutsideQuotes(cmd, spans, b.invocation)
          : matchesOutsideQuotes(cmd, spans, b.re)
        if (hit) {
          deny(event, b.msg)
          return
        }
      }
    })
  },
})
