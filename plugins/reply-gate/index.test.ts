import { beforeEach, describe, expect, test } from "bun:test"
import { existsSync, mkdtempSync, readFileSync, readdirSync, utimesSync, writeFileSync, mkdirSync } from "node:fs"
import { tmpdir } from "node:os"
import { join } from "node:path"
import plugin, { DONE, MARK, claimDir, gateOnTurnEnd, lastReply, pruneClaims, type Message } from "./index.ts"

// The real gate runs on these, so the tests also pin the plugin to its exit codes.
const BAD = "- **No gate on chat replies.** So the shape is: two sessions."
const GOOD = "The clinic opens at 9 on Monday. You still need the referral."

let log = ""
beforeEach(() => {
  log = join(mkdtempSync(join(tmpdir(), "reply-gate-")), "log.jsonl")
  process.env.REPLY_GATE_LOG = log
  delete process.env.REPLY_GATE_SCRIPT
})
const records = () => (existsSync(log) ? readFileSync(log, "utf8").trim().split("\n").map((l) => JSON.parse(l)) : [])

const user = (id: string, text: string, metadata?: Record<string, unknown>): Message => ({ id, type: "user", text, metadata })
const tool = (id: string): Message => ({ id, type: "assistant", content: [{ type: "tool" }] })
const said = (id: string, text: string): Message => ({ id, type: "assistant", content: [{ type: "text", text }] })
const idle: Message = { id: "idle", type: "idle" }

const harness = (messages: Message[], info: { parentID?: string } = {}) => {
  const prompts: Array<{ sessionID: string; text: string; metadata?: Record<string, unknown> }> = []
  const ctx = {
    state: { messages, info },
    session: {
      get: async () => ctx.state.info,
      context: async () => ctx.state.messages,
      prompt: async (input: { sessionID: string; text: string; metadata?: Record<string, unknown> }) => {
        prompts.push(input)
        return { id: "msg_prompt" }
      },
    },
  }
  return { ctx, prompts }
}

describe("the reply", () => {
  test("is the text after the turn's last tool call, with the last message's id", () => {
    const r = lastReply([user("u1", "Is it due?"), said("a1", "Checking."), tool("a2"), said("a3", GOOD), idle])
    expect(r).toEqual({ id: "a3", text: GOOD, secondPass: false })
  })

  test("is a second pass when the turn answers the gate's prompt, a tool call in between", () => {
    const r = lastReply([user("u2", "The reply gate ...", { [MARK]: { for: "a3" } }), tool("a4"), said("a5", BAD)])
    expect(r?.secondPass).toBe(true)
  })
})

describe("send once", () => {
  test("a flagged reply goes back once, marked, with the gate's reason", async () => {
    const h = harness([user("u1", "Is it due?"), said("a1", BAD), idle])
    const onIdle = gateOnTurnEnd(h.ctx)
    expect(await onIdle("ses_1")).toBe("sent")
    expect(await onIdle("ses_1")).toBe("skipped")
    expect(h.prompts).toHaveLength(1)
    expect(h.prompts[0].text).toContain("bold lead-in")
    expect(h.prompts[0].metadata).toEqual({ [MARK]: { for: "a1" } })
    const [r] = records()
    expect(r).toMatchObject({ harness: "opencode", session: "ses_1", message: "a1", blocked: true })
  })

  test("the rewrite is logged as the second pass and never sent back, flagged or not", async () => {
    const h = harness([user("u1", "Is it due?"), said("a1", BAD), user("u2", "The reply gate ...", { [MARK]: { for: "a1" } }), said("a2", BAD)])
    expect(await gateOnTurnEnd(h.ctx)("ses_1")).toBe("passed")
    expect(h.prompts).toHaveLength(0)
    expect(records()[0]).toMatchObject({ message: "a2", second_pass: true, blocked: false })
  })

  test("two instances on one turn, or a restart, send the reply back once and gate it once", async () => {
    // The server-wide event stream reaches the instance of every open folder (2026-11-28).
    const h = harness([user("u1", "Is it due?"), said("a1", BAD)])
    const results = await Promise.all([gateOnTurnEnd(h.ctx)("ses_1"), gateOnTurnEnd(h.ctx)("ses_1")])
    expect(results.sort()).toEqual(["sent", "skipped"])
    expect(await gateOnTurnEnd(h.ctx)("ses_1")).toBe("skipped")
    expect(h.prompts).toHaveLength(1)
    expect(records()).toHaveLength(1)
  })

  test("a claim older than 30 days is pruned and a fresh one is kept", () => {
    mkdirSync(claimDir(), { recursive: true })
    writeFileSync(join(claimDir(), "old"), "")
    writeFileSync(join(claimDir(), "new"), "")
    const t = (Date.now() - 31 * 86_400_000) / 1000
    utimesSync(join(claimDir(), "old"), t, t)
    pruneClaims()
    expect(readdirSync(claimDir())).toEqual(["new"])
  })

  test("a clean reply passes and nothing is sent", async () => {
    const h = harness([user("u1", "Is it due?"), said("a1", GOOD)])
    expect(await gateOnTurnEnd(h.ctx)("ses_1")).toBe("passed")
    expect(h.prompts).toHaveLength(0)
    expect(records()[0]).toMatchObject({ message: "a1", blocked: false, flags: 0 })
  })
})

describe("left alone", () => {
  test("a subagent's session and a turn with no text", async () => {
    const sub = harness([user("u1", "x"), said("a1", BAD)], { parentID: "ses_parent" })
    expect(await gateOnTurnEnd(sub.ctx)("ses_child")).toBe("skipped")
    const silent = harness([user("u1", "x"), tool("a1")])
    expect(await gateOnTurnEnd(silent.ctx)("ses_1")).toBe("skipped")
    expect(sub.prompts.length + silent.prompts.length).toBe(0)
    expect(records()).toHaveLength(0)
  })
})

describe("fail open", () => {
  test("a missing gate is logged and nothing is sent", async () => {
    process.env.REPLY_GATE_SCRIPT = join(tmpdir(), "no-such-reply-gate.py")
    const h = harness([user("u1", "x"), said("a1", BAD)])
    expect(await gateOnTurnEnd(h.ctx)("ses_1")).toBe("error")
    expect(h.prompts).toHaveLength(0)
    expect(records()[0]).toMatchObject({ source: "plugin", session: "ses_1", message: "a1" })
    expect(records()[0].error).toContain("gate exit 2")
  })

  test("a claim folder that cannot be written is logged and nothing is sent", async () => {
    const file = join(mkdtempSync(join(tmpdir(), "reply-gate-")), "not-a-folder")
    writeFileSync(file, "")
    process.env.REPLY_GATE_LOG = join(file, "log.jsonl")
    const h = harness([user("u1", "x"), said("a1", BAD)])
    expect(await gateOnTurnEnd(h.ctx)("ses_1")).toBe("error")
    expect(h.prompts).toHaveLength(0)
  })

  test("a failed read of the session is logged and nothing is sent", async () => {
    const h = harness([])
    h.ctx.session.context = async () => {
      throw new Error("server gone")
    }
    expect(await gateOnTurnEnd(h.ctx)("ses_1")).toBe("error")
    expect(h.prompts).toHaveLength(0)
    expect(records()[0]).toMatchObject({ source: "plugin", session: "ses_1", error: "server gone" })
  })

  test("a failed send is logged, and the reply is not sent at a later turn end", async () => {
    const h = harness([user("u1", "x"), said("a1", BAD)])
    let calls = 0
    h.ctx.session.prompt = async () => {
      calls++
      throw new Error("prompt refused")
    }
    const onIdle = gateOnTurnEnd(h.ctx)
    expect(await onIdle("ses_1")).toBe("error")
    expect(await onIdle("ses_1")).toBe("skipped")
    expect(calls).toBe(1)
    expect(records().at(-1)).toMatchObject({ source: "plugin", error: "prompt refused" })
  })
})

test("setup gates the reply when the turn succeeds, not on the deprecated idle event", async () => {
  const run = async (type: string) => {
    const h = harness([user("u1", "x"), said(`a_${type}`, BAD)])
    const ctx = { ...h.ctx, event: { subscribe: async function* () { yield { type, data: { sessionID: "ses_1" } } } } }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const cleanup = await plugin.setup(ctx as any)
    for (let i = 0; i < 25 && h.prompts.length === 0; i++) await new Promise((r) => setTimeout(r, 20))
    await cleanup?.()
    return h.prompts.length
  }
  expect(await run("session.idle")).toBe(0)
  expect(await run(DONE)).toBe(1)
})
