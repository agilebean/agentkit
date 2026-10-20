import { describe, expect, test } from "bun:test"
import plugin, { FALLBACK_AFTER, isConnectionFailure, stillOnFallback, waitedFor } from "./index"

describe("failure class", () => {
  test("a socket reset on the transport is the class that moves the session", () => {
    expect(
      isConnectionFailure({
        type: "provider.transport",
        message:
          "ECONNRESET: The socket connection was closed unexpectedly. For more information, pass `verbose: true` in the second argument to fetch()",
      }),
    ).toBe(true)
  })

  test("a header timeout is not", () => {
    expect(isConnectionFailure({ type: "provider.transport", message: "Timed out waiting for response headers" })).toBe(false)
  })

  test("a request the provider rejected is not", () => {
    expect(isConnectionFailure({ type: "provider.invalid-request", message: "ECONNRESET reported upstream" })).toBe(false)
  })
})

describe("budget", () => {
  test("four attempts is the 2 + 4 + 8 s of the runner's first three gaps", () => {
    expect(waitedFor(FALLBACK_AFTER)).toBe(14_000)
  })
})

describe("restore guard", () => {
  test("only a session still on the fallback model is pulled back", () => {
    expect(stillOnFallback({ providerID: "deepseek", id: "deepseek-flash" })).toBe(true)
    expect(stillOnFallback({ providerID: "opencode-go", id: "deepseek-v4.1-flash" })).toBe(false)
    expect(stillOnFallback({ providerID: "deepseek", id: "deepseek-v4-pro" })).toBe(false)
    expect(stillOnFallback(undefined)).toBe(false)
  })
})

// The hooks run against a stub, so the switch, the stored record and the
// restore are exercised without a server.
const harness = () => {
  const calls: Array<{ op: string; input: unknown }> = []
  const storage = new Map<string, unknown>()
  const hooks: Record<string, (input: unknown) => Promise<void> | void> = {}
  let model: { providerID: string; id: string; variant?: string } | undefined = {
    providerID: "opencode-go",
    id: "deepseek-v4.1-flash",
    variant: "high",
  }
  const ctx = {
    storage: {
      get: async (k: string) => storage.get(k),
      set: async (k: string, v: unknown) => void storage.set(k, v),
      remove: async (k: string) => void storage.delete(k),
      scan: async ({ prefix }: { prefix: string }) => ({
        entries: [...storage.entries()].filter(([k]) => k.startsWith(prefix)).map(([key, value]) => ({ key, value })),
      }),
    },
    session: {
      hook: async (name: string, callback: (input: unknown) => Promise<void> | void) => {
        hooks[name] = callback
        return { dispose: async () => undefined }
      },
      get: async () => ({ model }),
      switchModel: async ({ model: next }: { model: typeof model }) => {
        calls.push({ op: "switch", input: next })
        model = next
      },
    },
    event: { subscribe: async function* () {} },
  }
  return { ctx, hooks, calls, storage, model: () => model }
}

const reset = (message: string) => ({ type: "provider.transport", message })
const retry = (h: ReturnType<typeof harness>, sessionID = "ses_test") => ({
  sessionID,
  agent: "build",
  model: { providerID: "opencode-go", id: "deepseek-v4.1-flash", variant: "high" },
  error: reset("ECONNRESET: The socket connection was closed unexpectedly."),
  attempt: 1,
  decision: { retry: true, delay: 2000 } as { retry: boolean; delay?: number },
})

describe("failover", () => {
  test("four resets move the session to the direct API and the next attempt waits 1 s", async () => {
    const h = harness()
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    await plugin.setup(h.ctx as any)
    const input = retry(h)
    for (let i = 0; i < 3; i++) {
      input.decision = { retry: true, delay: 2000 }
      await h.hooks.retry(input)
    }
    expect(h.calls).toHaveLength(0)
    await h.hooks.retry(input)
    expect(h.calls).toHaveLength(1)
    expect(h.calls[0].input).toEqual({ providerID: "deepseek", id: "deepseek-flash", variant: "high" })
    expect(input.decision).toEqual({ retry: true, delay: 1000 })
    expect(h.storage.size).toBe(1)
  })

  test("the turn returning to idle puts the session back on the gateway", async () => {
    const h = harness()
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const cleanup = await plugin.setup(h.ctx as any)
    const input = retry(h)
    for (let i = 0; i < 4; i++) await h.hooks.retry(input)
    expect(h.model()?.providerID).toBe("deepseek")
    await h.ctx.storage.set("agentkit.provider-failover:ses_test", { from: { providerID: "opencode-go", id: "deepseek-v4.1-flash", variant: "high" }, at: 1 })
    await h.hooks.prompt({ sessionID: "ses_test", messageID: "m", prompt: { text: "" }, delivery: "queue" })
    expect(h.model()).toEqual({ providerID: "opencode-go", id: "deepseek-v4.1-flash", variant: "high" })
    expect(h.storage.size).toBe(0)
    await cleanup?.()
  })

  test("a model chosen during the fallback turn is left alone", async () => {
    const h = harness()
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    await plugin.setup(h.ctx as any)
    const input = retry(h)
    for (let i = 0; i < 4; i++) await h.hooks.retry(input)
    await h.ctx.session.switchModel({ model: { providerID: "deepseek", id: "deepseek-v4-pro" } })
    const switches = h.calls.length
    await h.hooks.prompt({ sessionID: "ses_test", messageID: "m", prompt: { text: "" }, delivery: "queue" })
    expect(h.calls.length).toBe(switches)
    expect(h.model()).toEqual({ providerID: "deepseek", id: "deepseek-v4-pro" })
  })

  test("a steer inside the fallback turn does not pull the session back", async () => {
    const h = harness()
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    await plugin.setup(h.ctx as any)
    const input = retry(h)
    for (let i = 0; i < 4; i++) await h.hooks.retry(input)
    const switches = h.calls.length
    await h.hooks.prompt({ sessionID: "ses_test", messageID: "m", prompt: { text: "" }, delivery: "steer" })
    expect(h.calls.length).toBe(switches)
  })
})
