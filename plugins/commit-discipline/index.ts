// commit-discipline — blocks wholesale git staging (`git add -A`, `git add .`,
// `git commit -a`), which would sweep unrelated working-tree edits into a task
// commit (RULES 10). Quoted text is inert: messages and echoes may name the
// blocked forms.

import { Plugin } from "@opencode/plugin"

const RULES: Array<{ re: RegExp; msg: string }> = [
  {
    re: /\bgit\s+add\s+(?:-A\b|--all\b|\.(?:\s|$))/,
    msg: "`git add -A` / `git add .` is blocked. Stage only the files YOU changed, by name (RULES 10).",
  },
  {
    re: /\bgit\s+commit\b[^\n|&;]*?(?:\s--all\b|\s-[a-zA-Z]*a[a-zA-Z]*\b)/,
    msg: "`git commit -a` is blocked. Stage explicitly, then commit (RULES 10).",
  },
]

// Spans of quoted text ('...' and "..."), including the quotes.
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

// A rule fires only when a match's start AND end both sit outside the quoted
// spans: a message the match merely passes through stays inert, while a real
// unquoted flag (`git commit -m "x" -a`) still blocks.
function triggersOutsideQuotes(
  cmd: string,
  spans: Array<[number, number]>,
  re: RegExp,
): boolean {
  const rx = new RegExp(re.source, re.flags.includes("g") ? re.flags : re.flags + "g")
  const inside = (at: number) => spans.some(([s, e]) => at >= s && at < e)
  let m: RegExpExecArray | null
  while ((m = rx.exec(cmd)) !== null) {
    const end = m.index + m[0].length - 1
    if (!inside(m.index) && !inside(end)) return true
    if (rx.lastIndex === m.index) rx.lastIndex += 1
  }
  return false
}

export default Plugin.define({
  id: "agentkit.commit-discipline",
  async setup(ctx) {
    await ctx.tool.hook("execute.before", (event) => {
      if (event.tool !== "shell") return
      const cmd = String((event.input as { command?: string } | undefined)?.command ?? "")
      const spans = quotedSpans(cmd)
      for (const r of RULES) if (triggersOutsideQuotes(cmd, spans, r.re)) throw new Error(r.msg)
    })
  },
})
