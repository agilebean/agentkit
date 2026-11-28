// reply-gate: opencode runs agentkit's reply gate (scripts/reply_gate.py, core 4)
// on every finished assistant reply, the way Claude Code runs it as a Stop hook
// (~/.claude/settings.json). Core 4 asks the agent to lint each reply with
// wording_lint.py, and an agent under a long task skips that step: on 627
// Claude Code replies 55% broke the standard (socrates agent/2026-11-28
// architecture review wording and common sense.md), and the 2026-11-27
// baseline failures ran in opencode on deepseek-v4.1-flash, which had no gate.
//
// When a turn succeeds (`session.execution.succeeded`; `session.idle` is
// deprecated in opencode's schema and v2.0.32 never emits it), the reply (the
// assistant's text after the turn's last tool call) goes to the gate on stdin.
// The gate exits 2 with the reason on stdout when it finds a flag; the reason
// goes back into the same session once, as a prompt marked with
// `metadata["agentkit.reply-gate"]`, and the agent posts the reply again,
// rewritten. Chaehan chose "block and resend" (2026-11-28): one rewrite, never
// two. So every reply message id is gated once, and the reply to a marked
// prompt is a second pass, which the gate logs and never sends back.
//
// Once means once across instances. The event stream is server-wide, and the
// server loads the plugin once per open folder, so every instance sees every
// session's turn; two servers (the CLI's service and OpenChamber's) share the
// config. On 2026-11-28 the first headless run sent one reply back twice, from
// the instance of the test folder and the one of a socrates worktree. The one
// instance that creates the reply's claim file (exclusive create, kept in
// ~/.cache/agentkit/reply-gate/claims/) runs the gate; every other instance,
// and a restart, finds the file and skips the reply.
//
// A subagent's session is left alone: its reply goes to the parent agent, not
// to Chaehan (the Claude Code gate skips sidechains for the same reason).
//
// The plugin fails open. An error (the gate missing, a timeout, an exit code
// other than 0 or 2, a failed read, claim or send) is logged to the gate's
// log, ~/.cache/agentkit/reply-gate/log.jsonl, and nothing is sent.
//
// A one-shot `opencode run --standalone` stops its private server about 50 ms
// after the reply, before the gate has run, so the gate acts only where the
// server outlives the turn: the background service, the TUI and OpenChamber.

import { Plugin } from "@opencode/plugin"
import { spawn } from "node:child_process"
import { appendFileSync, closeSync, mkdirSync, openSync, readdirSync, statSync, unlinkSync } from "node:fs"
import { homedir } from "node:os"
import { dirname, join } from "node:path"
import { fileURLToPath } from "node:url"

/** The metadata key of the prompt that sends a reply back. */
export const MARK = "agentkit.reply-gate"
/** The event that ends a turn that succeeded. */
export const DONE = "session.execution.succeeded"
const CLAIM_DAYS = 30
const TIMEOUT_MS = 20_000

// $HOME first: the runtime caches homedir(), and the gate (Python) reads $HOME too.
const home = () => process.env.HOME || homedir()
export const gateScript = () =>
  process.env.REPLY_GATE_SCRIPT || fileURLToPath(new URL("../../scripts/reply_gate.py", import.meta.url))
export const logPath = () => process.env.REPLY_GATE_LOG || join(home(), ".cache/agentkit/reply-gate/log.jsonl")
const python = () => process.env.REPLY_GATE_PYTHON || "python3"
export const claimDir = () => join(dirname(logPath()), "claims")

/** True for the one caller, in any instance or process, that claims this reply. */
export function claim(messageID: string): boolean {
  const dir = claimDir()
  mkdirSync(dir, { recursive: true })
  try {
    closeSync(openSync(join(dir, messageID.replace(/[^\w-]/g, "_")), "wx"))
    return true
  } catch (error) {
    if ((error as { code?: string }).code === "EEXIST") return false
    throw error
  }
}

/** Claims older than CLAIM_DAYS go: a reply that old never ends a turn again. */
export function pruneClaims(now = Date.now()): void {
  try {
    const dir = claimDir()
    for (const name of readdirSync(dir)) {
      const file = join(dir, name)
      if (now - statSync(file).mtimeMs > CLAIM_DAYS * 86_400_000) unlinkSync(file)
    }
  } catch {
    // no claims yet, or one went between the read and the delete
  }
}

type Block = { type: string; text?: string }
export type Message = {
  id: string
  type: string
  text?: string
  content?: Block[]
  metadata?: Record<string, unknown>
}
export type Reply = { id: string; text: string; secondPass: boolean }

// Messages that sit inside or after a turn without being a turn's input.
const BOOKKEEPING = new Set([
  "idle",
  "system",
  "agent-switched",
  "model-switched",
  "agent-selected",
  "model-selected",
  "location-switched",
])

/**
 * The turn's reply: the text of the trailing assistant messages after the
 * turn's last tool call, with the id of the last assistant message. It is a
 * second pass when the turn's user message is the gate's own prompt, which
 * holds when the rewrite ran a tool first.
 */
export function lastReply(messages: Message[]): Reply | undefined {
  const texts: string[] = []
  let id: string | undefined
  let i = messages.length - 1
  for (; i >= 0; i--) {
    const m = messages[i]
    if (m.type === "assistant") {
      id ??= m.id
      const blocks = m.content ?? []
      let tool = false
      for (let j = blocks.length - 1; j >= 0; j--) {
        if (blocks[j].type === "tool") {
          tool = true
          break
        }
        if (blocks[j].type === "text" && blocks[j].text?.trim()) texts.push(blocks[j].text!)
      }
      if (tool) break
      continue
    }
    if (BOOKKEEPING.has(m.type)) continue
    break
  }
  if (!id) return undefined
  let secondPass = false
  for (; i >= 0; i--) {
    if (messages[i].type !== "user") continue
    secondPass = Boolean(messages[i].metadata?.[MARK])
    break
  }
  return { id, text: texts.reverse().join("\n\n"), secondPass }
}

export type GateResult = { code: number | null; out: string; err: string }

/** One run of the gate in harness mode: the reply on stdin, the decision in the exit code. */
export function runGate(text: string, args: string[], script = gateScript()): Promise<GateResult> {
  return new Promise((resolve, reject) => {
    const child = spawn(python(), [script, "--harness", "opencode", ...args, "-"], { stdio: ["pipe", "pipe", "pipe"] })
    let out = ""
    let err = ""
    const timer = setTimeout(() => {
      child.kill("SIGKILL")
      reject(new Error(`gate timed out after ${TIMEOUT_MS} ms`))
    }, TIMEOUT_MS)
    child.stdout.on("data", (d) => (out += d))
    child.stderr.on("data", (d) => (err += d))
    child.on("error", (error) => {
      clearTimeout(timer)
      reject(error)
    })
    child.on("close", (code) => {
      clearTimeout(timer)
      resolve({ code, out, err })
    })
    child.stdin.on("error", () => undefined)
    child.stdin.end(text)
  })
}

export function logError(record: Record<string, unknown>): void {
  try {
    const path = logPath()
    mkdirSync(dirname(path), { recursive: true })
    const time = new Date().toISOString().slice(0, 19)
    appendFileSync(path, JSON.stringify({ time, harness: "opencode", source: "plugin", ...record }) + "\n")
  } catch {
    // a log failure must never break a session
  }
}

const message = (error: unknown) => (error instanceof Error ? error.message : String(error))

type Ctx = {
  session: {
    get(input: { sessionID: string }): Promise<{ parentID?: string } | undefined>
    context(input: { sessionID: string }): Promise<Message[]>
    prompt(input: { sessionID: string; text: string; metadata?: Record<string, unknown> }): Promise<unknown>
  }
}

/** The turn-end handler: gate the session's reply once and send a flagged one back. */
export function gateOnTurnEnd(ctx: Ctx) {
  return async (sessionID: string): Promise<"sent" | "passed" | "skipped" | "error"> => {
    let reply: Reply | undefined
    try {
      const info = await ctx.session.get({ sessionID })
      if (info?.parentID) return "skipped"
      reply = lastReply((await ctx.session.context({ sessionID })) ?? [])
      if (!reply || !reply.text.trim()) return "skipped"
      // Claimed before the gate runs, so no instance gates or sends one reply twice.
      if (!claim(reply.id)) return "skipped"

      const args = ["--session", sessionID, "--message", reply.id, ...(reply.secondPass ? ["--second-pass"] : [])]
      const result = await runGate(reply.text, args)
      if (result.code === 0) return "passed"
      if (result.code !== 2 || !result.out.trim() || reply.secondPass) {
        logError({
          session: sessionID,
          message: reply.id,
          error: `gate exit ${result.code}: ${(result.err || result.out).trim().slice(0, 300)}`,
        })
        return "error"
      }
      await ctx.session.prompt({ sessionID, text: result.out.trim(), metadata: { [MARK]: { for: reply.id } } })
      return "sent"
    } catch (error) {
      logError({ session: sessionID, message: reply?.id, error: message(error).slice(0, 300) })
      return "error"
    }
  }
}

export default Plugin.define({
  id: "agentkit.reply-gate",
  async setup(ctx) {
    const stop = new AbortController()
    const onTurnEnd = gateOnTurnEnd(ctx as unknown as Ctx)
    pruneClaims()

    void (async () => {
      try {
        for await (const event of ctx.event.subscribe({ signal: stop.signal })) {
          if (event.type !== DONE) continue
          const sessionID = (event as { data?: { sessionID?: string } }).data?.sessionID
          // Not awaited: one session's gate run never holds up another session's event.
          if (sessionID) void onTurnEnd(sessionID)
        }
      } catch (error) {
        if (!stop.signal.aborted) logError({ error: `event stream ended: ${message(error)}` })
      }
    })()

    return () => {
      stop.abort()
    }
  },
})
