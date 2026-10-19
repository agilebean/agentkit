import { Plugin } from "@opencode/plugin"
import { readFileSync } from "node:fs"

// --- detection -------------------------------------------------------------
//
// One flat ceiling is not detection. On 2026-10-20 an osascript that opened a
// quarantined deck copy sat silent for 120 s (AppleScript's per-event default),
// was cut at the 60 s cap, and the harness's own words -- "Retry with a larger
// timeout" -- sent the pass back with 180 s, then to a background relaunch and a
// sleep-poll: three sends of one event to one file. A ceiling bounds how long
// the agent waits; it says nothing about what class of work is running, whether
// the script can block at all, or whether this is the same target as the last
// attempt. So the guard now carries four things instead:
//
//   1. a class ladder -- the cap is the class's own measured p90, not 60 s;
//   2. an in-script per-event bound for any script that opens or writes a
//      document (15 s instead of the app's 120 s default);
//   3. a supervisor -- app automation and renders run as a watched child that
//      is killed at the cap and answers with a stop message, not a retry hint;
//   4. a target-identity repeat guard -- the same file or app addressed by a
//      rewritten command is still the same attempt.
//
// Measured over 4007 shell calls (2026-10-13 to 2026-10-20): osascript p50
// 0.6 s / p90 20.3 s; python and renders p90 9.0 s / p99 55 s; builds p99
// 4.5 s; inspection p90 0.5 s. 42 calls hit their timeout.

const WATCHDOG_SLACK_MS = 5_000
const APP_EVENT_MS = 15_000
const APP_EVENT_CEILING_MS = 60_000
const DEFAULT_TIMEOUT_MS = 20_000

interface CmdClass {
  name: string
  ms: number
  supervise: boolean
}

const CLASS_RULES: Array<{ name: string; re: RegExp; ms: number; supervise: boolean; firstLineOnly?: boolean }> = [
  { name: "app automation", re: /\bosascript\b|\bopen\s+-a\b/, ms: 20_000, supervise: true },
  {
    name: "render/pipeline",
    re: /render\.py|pipeline\.py|\bmamba run\b|\bpython3?\b|\bbrave\b|\bplaywright\b/,
    ms: 60_000,
    supervise: true,
  },
  { name: "build/install", re: /\b(npm|bun|git|ditto|rsync|pip3?|pytest|make|cargo|go)\b/, ms: 30_000, supervise: false },
  {
    name: "inspection",
    re: /^\s*(ls|cat|rg|fd|sed|grep|file|xattr|du|head|tail|wc|stat|date|pwd|echo|printf|test|mkdir|cp|mv|rm|unzip|zip)\b/,
    ms: 10_000,
    supervise: false,
    firstLineOnly: true,
  },
]

function classify(cmd: string): CmdClass {
  const first = cmd.split("\n").find((l) => l.trim()) ?? ""
  for (const c of CLASS_RULES) {
    if (c.re.test(c.firstLineOnly ? first : cmd)) return { name: c.name, ms: c.ms, supervise: c.supervise }
  }
  return { name: "default", ms: DEFAULT_TIMEOUT_MS, supervise: false }
}

/** Quoted text is data: a command that merely prints or seds a string naming
 * osascript is not app automation. Classification runs on the unquoted part. */
function stripQuoted(cmd: string, spans: Array<[number, number]>): string {
  if (!spans.length) return cmd
  let out = ""
  let i = 0
  for (const [s, e] of spans) {
    out += cmd.slice(i, s) + " "
    i = e
  }
  return out + cmd.slice(i)
}

// A script handed to osascript is data inside quotes, so a bound it carries in a
// file on disk is invisible to a regex run over the command. Read the payloads
// a command names, and skip the ones that are not files.
function scriptsOnDisk(cmd: string): string {
  let text = ""
  for (const m of cmd.matchAll(/([^\s'"`;|&()<>]+\.(?:applescript|scpt|applescript\.txt))/g)) {
    try {
      text += "\n" + readFileSync(m[1], "utf8")
    } catch {
      // not a path, or unreadable: the command text is all we have
    }
  }
  return text
}

const APP_WRITE_RE = /\b(open|export|save|close|print|duplicate|delete|make\s+new)\b/
const BOUND_RE = /with timeout of\s+(\d+)/g

function bounds(text: string): number[] {
  const out: number[] = []
  for (const m of text.matchAll(BOUND_RE)) out.push(Number(m[1]))
  return out
}

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
    re: /with timeout of\s+(?:[6-9]\d|\d{3,})/,
    invocation: /\bosascript\b/,
    msg:
      "Blocked by agentkit.shell-guard: `with timeout of` above 60 s. An app " +
      "event that needs more than 15 s is wedged, not slow: cap it at 15 and run " +
      "long app automation in the background with a progress log (RULES 73/166).",
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
  appTargets: Map<string, number>
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
      appTargets: new Map(),
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

/** The supervisor: the class's cap is enforced here, by us, not by the harness.
 * Output is buffered into a temp file and replayed at the end, which is where a
 * foreground call puts it anyway. A kill answers with what to do next, never
 * with "retry with a larger timeout" -- that sentence is what sent the
 * 2026-10-20 pass back into the same wedged event three times. */
function withWatchdog(cmd: string, line: string, cls: CmdClass): string {
  const ticks = Math.max(2, Math.round(cls.ms / 500))
  const stop =
    cls.name === "app automation"
      ? `[agentkit] killed at ${cls.ms / 1000} s: the app never answered the event. ` +
        `Do not re-send it. Read the input (xattr, file) and the app with a read-only ` +
        `probe that carries its own bound (with timeout of 5 seconds ... count of documents) ` +
        `before any second send (RULES 73/166).`
      : `[agentkit] killed at ${cls.ms / 1000} s: this did not finish. Run it in the ` +
        `background with a progress log and read the log; a longer timeout is not the fix (RULES 73).`
  const esc = (s: string) => s.replace(/'/g, `'\\''`)
  return [
    `__ak_out=$(mktemp)`,
    `{`,
    cmd,
    `} >"$__ak_out" 2>&1 &`,
    `__ak_pid=$!`,
    `__ak_n=0`,
    `while kill -0 "$__ak_pid" 2>/dev/null; do`,
    `  sleep 0.5`,
    `  __ak_n=$((__ak_n+1))`,
    `  if [ "$__ak_n" -ge ${ticks} ]; then`,
    `    kill -9 "$__ak_pid" 2>/dev/null`,
    `    wait "$__ak_pid" 2>/dev/null`,
    `    cat "$__ak_out"`,
    `    rm -f "$__ak_out"`,
    `    printf '\\n%s\\n' '${esc(stop)}' >&2`,
    `    exit 124`,
    `  fi`,
    `done`,
    `wait "$__ak_pid"`,
    `__ak_rc=$?`,
    `cat "$__ak_out"`,
    `rm -f "$__ak_out"`,
    `printf '\\n%s\\n' '${esc(line)}' >&2`,
    `exit $__ak_rc`,
  ].join("\n")
}

/** The targets an app-automation command addresses: the absolute paths it hands
 * to the app. The exact-text repeat guard misses the case that matters - the
 * same file re-sent under `nohup`, a bigger timeout, or a renamed script - and
 * the app's name is not a target: addressing Keynote twice for two different
 * files is ordinary work, addressing one file twice is the retry. */
function targets(cmd: string): string[] {
  const out = new Set<string>()
  for (const m of cmd.matchAll(/(?:^|[\s'"(=])((?:\/Users|\/tmp|\/Volumes|\/private)\/[^\s'";|&)]+)/g)) out.add(m[1])
  return [...out].sort()
}

const TARGET_WARN_AT = 2
const TARGET_DENY_AT = 3

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
      const cmd = event.command ?? ""
      const spans = quotedSpans(cmd)
      const cls = classify(stripQuoted(cmd, spans))

      // 1) the class ladder. A supervised class owns its own bound, so the tool
      // is given slack and our kill lands first; every other class keeps the
      // requested timeout when it is smaller than the class cap.
      if (event.timeout !== 0) {
        if (cls.supervise) {
          event.timeout = cls.ms + WATCHDOG_SLACK_MS
        } else if (typeof event.timeout === "number") {
          event.timeout = Math.min(event.timeout, cls.ms)
        } else {
          event.timeout = cls.ms
        }
      }

      // 2) a script that opens or writes a document must carry its own per-event
      // bound: without one the app's default is 120 s of silence (RULES 73/166).
      if (/\bosascript\b/.test(cmd) && matchesOutsideQuotes(cmd, spans, /\bosascript\b/)) {
        const payload = cmd + scriptsOnDisk(cmd)
        if (APP_WRITE_RE.test(payload)) {
          const found = bounds(payload)
          const largest = found.length ? Math.max(...found) : 0
          if (largest === 0 || largest > APP_EVENT_MS / 1000) {
            deny(
              event,
              "Blocked by agentkit.shell-guard: this script opens or writes a " +
                "document and carries no per-event timeout, so the app's own " +
                "default is 120 s and a wedged event reads as a hang. Wrap the app " +
                "block in `with timeout of 15 seconds` ... `end timeout`, and put the " +
                "input checks (xattr, file) before it (RULES 73/166).",
            )
            return
          }
        }
      }

      // 3) deny banned patterns; quoted text is inert (osascript payload aside)
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

      // 4) the ledger: count the call, refuse the fourth identical command in
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

      // 5) app automation is also keyed by the target it addresses: the same
      // file or app under a rewritten command is still the same attempt.
      let targetNote = ""
      if (cls.name === "app automation") {
        for (const t of targets(cmd)) {
          const n = (led.appTargets.get(t) ?? 0) + 1
          if (led.appTargets.size > MAX_SEEN) led.appTargets.clear()
          led.appTargets.set(t, n)
          if (n >= TARGET_DENY_AT) {
            deny(
              event,
              `Blocked by agentkit.shell-guard: ${t} has already been addressed ` +
                `${n - 1} times in this turn by app automation (RULES 73: two ` +
                `attempts on one deliverable, and a rewritten command - nohup, a ` +
                `bigger timeout, a renamed script - does not reset the count). If ` +
                `the app did not answer, read the input (xattr, file) and probe the ` +
                `app with a bounded read-only event; do not send the same event again.`,
            )
            return
          }
          if (n === TARGET_WARN_AT) {
            targetNote =
              `\n[agentkit] ${t} is on its second app-automation send this turn ` +
              `(RULES 73). The third is refused: read the input and probe the app first.`
          }
        }
      }

      const { base, gate } = ledgerLine(sid, led, Date.now())
      let line = gate ? `${base}\n${gate}` : base
      if (seen === REPEAT_WARN_AT) {
        line +=
          `\n[agentkit] this exact command is on its ${seen}rd run this turn ` +
          `(RULES 73). The fourth is refused: rename the approach instead.`
      }
      led.last = Date.now()
      line += targetNote
      event.command = cls.supervise ? withWatchdog(cmd, line, cls) : withLedger(cmd, line)
    })
  },
})
