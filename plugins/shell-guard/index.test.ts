import { expect, test } from "bun:test"
import plugin from "./index.ts"

// The plugin is loaded as `Plugin.define({ id, setup })` in opencode 2.0.20.
// This harness supplies the four hook registries the pass uses and drives them
// the way the host does: mutate the event object, read it back.

type Handler = (event: any) => unknown

function fakeCtx() {
  const hooks: Record<string, Handler[]> = {}
  const reg = (domain: string) => async (name: string, fn: Handler) => {
    ;(hooks[`${domain}:${name}`] ??= []).push(fn)
  }
  const ctx: any = {
    session: { hook: reg("session") },
    tool: { hook: reg("tool") },
    shell: { hook: reg("shell") },
  }
  const fire = async (name: string, event: any) => {
    for (const fn of hooks[name] ?? []) await fn(event)
    return event
  }
  return { ctx, fire }
}

const SHELL = "shell"

let turn = 0

async function setup() {
  const { ctx, fire } = fakeCtx()
  await (plugin as any).setup(ctx)
  // A fresh session id per test: the ledger is keyed by session and lives in
  // module state, exactly as it does in the host.
  const sid = `ses_test_${++turn}`
  return {
    /** one shell call, as the host presents it */
    shell: async (command: string, session = sid, timeout = 20_000) => {
      const event = { command, cwd: "/tmp", timeout, shell: "zsh", env: { OPENCODE_SESSION_ID: session } }
      await fire("tool:execute.before", {
        tool: SHELL,
        sessionID: session,
        agent: "a",
        messageID: "m",
        id: `c${Math.random()}`,
        input: {},
      })
      await fire("shell:create.before", event)
      return event
    },
    /** one non-shell tool call */
    other: async (tool: string, session = sid) => {
      const id = `c${Math.random()}`
      await fire("tool:execute.before", { tool, sessionID: session, agent: "a", messageID: "m", id, input: {} })
      await fire("tool:execute.after", { tool, sessionID: session, status: "completed", id, input: {} })
    },
    /** a new user prompt = a new turn */
    prompt: async (session = sid) => {
      await fire("session:prompt", { sessionID: session, messageID: "m" })
    },
    sid,
  }
}

test("a command still runs, and its exit code survives the ledger wrapper", async () => {
  const h = await setup()
  const e = await h.shell("exit 3")
  const cmd: string = e.command
  expect(cmd.startsWith("exit 3\n")).toBe(true)
  expect(cmd).toContain("__agentkit_rc=$?")
  expect(cmd.trimEnd().endsWith("exit $__agentkit_rc")).toBe(true)
  // the ledger line is printed on stderr, after the command's own output
  expect(cmd).toContain(">&2")
})

test("every shell result carries the count, the clock and the machine seconds", async () => {
  const h = await setup()
  const first = await h.shell("echo one")
  expect(first.command).toContain("[agentkit] call 1 - t+0.0 min this turn - tools")
  const second = await h.shell("echo two")
  expect(second.command).toContain("[agentkit] call 2 - t+")
})

test("non-shell tools are counted too", async () => {
  const h = await setup()
  await h.other("read")
  await h.other("edit")
  const e = await h.shell("echo x")
  expect(e.command).toContain("[agentkit] call 3 ")
})

test("the go-gate states itself at 15 calls, once", async () => {
  const h = await setup()
  let seen = ""
  for (let i = 0; i < 15; i++) seen = (await h.shell(`echo call-${i}`)).command
  expect(seen).toContain("call 15 ")
  expect(seen).toContain("go-gate (RULES 75)")
  const next = await h.shell("echo after")
  expect(next.command).toContain("call 16 ")
  expect(next.command).not.toContain("go-gate")
})

test("the 30-call rung names rule 74's batching", async () => {
  const h = await setup()
  let seen = ""
  for (let i = 0; i < 30; i++) seen = (await h.shell(`echo n-${i}`)).command
  expect(seen).toContain("30 tool calls (RULES 74)")
})

test("a new prompt restarts the turn ledger", async () => {
  const h = await setup()
  await h.shell("echo a")
  await h.prompt()
  const e = await h.shell("echo b")
  expect(e.command).toContain("[agentkit] call 1 ")
})

test("the fourth identical command in a turn is refused", async () => {
  const h = await setup()
  const one = await h.shell("ls -la")
  const two = await h.shell("ls -la")
  const three = await h.shell("ls -la")
  const four = await h.shell("ls -la")
  expect(one.command).not.toContain("Blocked")
  expect(two.command).not.toContain("Blocked")
  expect(three.command).toContain("is on its 3rd run this turn")
  expect(four.command).toContain("Blocked by agentkit.shell-guard")
  expect(four.command).toContain("at most two attempts")
  // a different command in the same turn is untouched
  expect((await h.shell("ls -la /tmp")).command).not.toContain("Blocked")
})

test("the ledger wraps a command without running it twice or losing stdout", async () => {
  const h = await setup()
  const e = await h.shell("printf 'a\\nb\\n'")
  const body = e.command.split("\n__agentkit_rc=$?")[0]
  expect(body).toBe("printf 'a\\nb\\n'")
})

test("timeouts are still capped at 60 s, and banned searches still denied", async () => {
  const h = await setup()
  const long = await h.shell("node -e 1", "ses_test", 300_000)
  expect(long.timeout).toBe(60_000)
  const denied = await h.shell("grep -rn foo ~/Library")
  expect(denied.command).toContain("Blocked by agentkit.shell-guard")
  expect(denied.command).toContain("rg")
})

test("quoted text stays inert: a command mentioning grep -r is not denied", async () => {
  const h = await setup()
  const e = await h.shell(`echo 'grep -rn foo ~/Library'`)
  expect(e.command).not.toContain("Blocked")
})
