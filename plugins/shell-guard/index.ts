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

// --- the call ledger: rules 73/74/75's count and clock ----------------------
//
// Rules 73, 74 and 75 cap a pass by its tool-call count and require the
// elapsed clock to be visible. Both facts were invisible until a pass chose to
// measure itself, and on 2026-10-17 the E08 deck pass ran 230 calls and 74
// minutes with no cost line, no go-gate and no clock: 54 min of that was
// model latency over 198 steps. So the count and the clock ride the tool
// output itself - a line the agent reads whether or not it remembered the
// rule - and the ladder states the gate in the output at the call where it
// applies.

const TURN_GAP_MS = 15 * 60_000
const GO_GATE_LADDER = [15, 30, 60, 100, 200]
const REPEAT_WARN_AT = 3
const REPEAT_DENY_AT = 4
const MAX_LEDGERS = 50
const MAX_SEEN = 500

const GATE: Record<number, string> = {
  15:
    "[agentkit] go-gate (RULES 75): 15 tool calls in this turn. A pass past ~15 " +
    "calls opens with a cost line (calls, machine seconds, app launches) in the " +
    "reply and stops for the user's go. State it now, or say in one line why " +
    "this pass is small.",
  30:
    "[agentkit] 30 tool calls (RULES 74): one script per analysis, one result " +
    "read per change set, one question batch. Name the calls that are left and " +
    "cut them into one batch.",
  60:
    "[agentkit] 60 tool calls: at ~15 s of model latency per round trip this " +
    "turn has already spent ~15 min of wall clock. Stop, report what is done " +
    "and what is left.",
  100:
    "[agentkit] 100 tool calls in one turn (RULES 75: stop at twice the stated " +
    "cost). Report now; a pass this size is a rebuilt approach, not a longer one.",
  200:
    "[agentkit] 200 tool calls in one turn. Stop the pass and report: the call " +
    "count is the wall clock.",
}

interface Ledger {
  turnStart: number
  last: number
  calls: number
  toolMs: number
  warned: Set<number>
  seen: Map<string, number>
  pending: Map<string, number>
}

const ledgers = new Map<string, Ledger>()

function ledger(sid: string): Ledger {
  const now = Date.now()
  let led = ledgers.get(sid)
  if (!led || now - led.last > TURN_GAP_MS) {
    if (ledgers.size >= MAX_LEDGERS) {
      const oldest = [...ledgers.entries()].sort((a, b) => a[1].last - b[1].last)[0]
      if (oldest) ledgers.delete(oldest[0])
    }
    led = {
      turnStart: now,
      last: now,
      calls: 0,
      toolMs: 0,
      warned: new Set(),
      seen: new Map(),
      pending: new Map(),
    }
    ledgers.set(sid, led)
  }
  return led
}

/** The line every shell result carries: the call count, the turn clock, and
 * the round trip since the previous call - the two facts rules 73/74/75 cap a
 * pass by, and the latency they are made of. At a ladder rung it adds the rule
 * that now applies. */
function ledgerLine(sid: string, led: Ledger, now: number): { base: string; gate: string | null } {
  const mins = (now - led.turnStart) / 60_000
  const round = led.calls > 1 ? (now - led.last) / 1000 : null
  const parts = [
    `call ${led.calls}`,
    `t+${mins.toFixed(1)} min this turn`,
    `tools ${(led.toolMs / 1000).toFixed(1)} s`,
  ]
  if (round !== null) parts.push(`+${round.toFixed(0)} s since the last call`)
  const base = `[agentkit] ${parts.join(" - ")}`
  for (const n of GO_GATE_LADDER) {
    if (led.calls >= n && !led.warned.has(n)) {
      led.warned.add(n)
      return { base, gate: GATE[n] }
    }
  }
  return { base, gate: null }
}

/** Run the command, keep its exit code, print the ledger line on stderr. */
function withLedger(cmd: string, line: string): string {
  const esc = line.replace(/'/g, `'\\''`)
  return `${cmd}\n__agentkit_rc=$?\nprintf '\\n%s\\n' '${esc}' >&2\nexit $__agentkit_rc`
}

function norm(cmd: string): string {
  return cmd.replace(/\s+/g, " ").trim().slice(0, 400)
}

export default Plugin.define({
  id: "agentkit.shell-guard",
  async setup(ctx) {
    // A new prompt is a new turn: the ledger restarts there, and the 15-minute
    // gap check in ledger() is the fallback when the hook does not fire.
    await ctx.session.hook("prompt", (event) => {
      ledgers.delete(event.sessionID)
    })

    // Every non-shell tool call is counted here; the shell's own count happens
    // in create.before, where the command and its session are both in hand.
    await ctx.tool.hook("execute.before", (event) => {
      const led = ledger(event.sessionID)
      led.pending.set(event.id, Date.now())
      if (event.tool !== "shell") {
        led.calls += 1
        led.last = Date.now()
      }
    })

    // Machine seconds per call, so the ledger can carry rule 74's second
    // number (the measured machine time) as well as its first (the count).
    await ctx.tool.hook("execute.after", (event) => {
      const led = ledgers.get(event.sessionID)
      if (!led) return
      const started = led.pending.get(event.id)
      if (started) {
        led.toolMs += Date.now() - started
        led.pending.delete(event.id)
      }
    })

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
      if (!cmd.trim()) return

      // 3) the ledger: count the call, refuse the fourth identical command in
      // one turn (rule 73's two-attempt budget), and write the clock and the
      // count into the result the agent is about to read.
      const sid = event.env?.OPENCODE_SESSION_ID ?? "unknown"
      const led = ledger(sid)
      led.calls += 1

      const key = norm(cmd)
      const seen = (led.seen.get(key) ?? 0) + 1
      if (led.seen.size > MAX_SEEN) led.seen.clear()
      led.seen.set(key, seen)
      if (seen >= REPEAT_DENY_AT) {
        deny(
          event,
          `Blocked by agentkit.shell-guard: this exact command has run ${seen} ` +
            `times in this turn (RULES 73: one tool gets at most two attempts on ` +
            `one deliverable, and rewriting the command does not reset the ` +
            `count). Change the approach, or say in the reply why this repeat ` +
            `is new work.`,
        )
        return
      }

      const { base, gate } = ledgerLine(sid, led, Date.now())
      let line = gate ? `${base}\n${gate}` : base
      if (seen === REPEAT_WARN_AT) {
        line +=
          `\n[agentkit] this exact command is on its ${seen}rd run this turn ` +
          `(RULES 73). The fourth is refused: rename the approach instead.`
      }
      led.last = Date.now()
      event.command = withLedger(cmd, line)
    })
  },
})
