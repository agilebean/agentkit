// mcp-reconnect — a failed MCP connection does not stay failed for the life of
// its location.
//
// The service connects a location's MCP servers when that location boots, and
// locations are evicted and re-booted constantly. A connect that lands on a
// network transition (DNS mid-switch, a connect timeout, a socket reset) is
// recorded as `failed`, and nothing retries it: that one project keeps missing
// its tools while its neighbours reconnect. This plugin watches the status and
// forces a fresh reconciliation.
//
// Ported 2026-10-12 from the V1 plugin that sat unregistered at
// ~/.config/openchamber/mcp-reconnect/openchamber-mcp-reconnect-plugin.js
// (V1 plugin functions do not execute on opencode V2, and V2 exposes no mcp
// connect call: a server's lifecycle follows its configuration, so the cycle
// here disables the server through a transform, reloads, drops the transform,
// and reloads again to make it connect). Registered in
// ~/.config/opencode/opencode.jsonc under `plugins`, as a global entry, so every
// location gets its own instance.

import { Plugin } from "@opencode/plugin"

const INITIAL_RETRY_MS = 1_000
const MAX_RETRY_MS = 30_000
const SLOW_RETRY_MS = 300_000
const FAST_ATTEMPTS = 10
const IDLE_CHECK_MS = 30_000
// A location can hold several instances of this plugin (a location reload does
// not always tear the old ones down), and each would otherwise retry the same
// server on its own schedule. Instances share this floor through plugin storage,
// so the aggregate rate stays bounded no matter how many are alive.
const ATTEMPT_FLOOR_MS = 10_000

type ListedServer = { name: string; status?: { status?: string; error?: string } }

export default Plugin.define({
  id: "agentkit.mcp-reconnect",
  async setup(ctx) {
    const directory = ctx.location.directory
    let disposed = false
    let running = false
    let wakeRequested = false
    let timer: ReturnType<typeof setTimeout> | undefined
    // Consecutive attempts per server, cleared as soon as it reads healthy.
    const attempts = new Map<string, number>()
    const dueAt = new Map<string, number>()

    const schedule = (delayMs: number) => {
      if (disposed) return
      if (timer !== undefined) clearTimeout(timer)
      timer = setTimeout(() => void tick(), delayMs)
    }

    // A status change beats waiting out the interval; a tick already in flight
    // picks the request up when it finishes.
    const wake = () => {
      if (running) {
        wakeRequested = true
        return
      }
      schedule(INITIAL_RETRY_MS)
    }

    // Disable through a transform, reload, drop the transform, reload. The
    // second reload reconciles the server from its configured state, and a
    // server that is not disabled is allowed to connect again. Both reloads run
    // even if an earlier step fails: a plugin bug must never leave a server
    // disabled.
    const reconnect = async (name: string) => {
      try {
        const off = await ctx.mcp.transform((editor) => {
          if (!editor.get(name)) return
          editor.update(name, (config) => {
            config.disabled = true
          })
        })
        try {
          await ctx.mcp.reload()
        } finally {
          await off.dispose().catch(() => undefined)
        }
      } finally {
        await ctx.mcp.reload().catch(() => undefined)
      }
    }

    // Claim the right to make the next attempt for this location. Every live
    // instance reads the same key, so one attempt clears the floor for all of
    // them. When storage cannot be read the plugin proceeds rather than stall.
    const claimAttempt = async () => {
      const key = `attempt:${directory}`
      try {
        const last = Number(await ctx.storage.get(key)) || 0
        const now = Date.now()
        if (now - last < ATTEMPT_FLOOR_MS) return false
        await ctx.storage.set(key, now)
        return true
      } catch {
        return true
      }
    }

    const tick = async () => {
      if (running) {
        wakeRequested = true
        return
      }
      running = true
      let delay = IDLE_CHECK_MS
      try {
        const listed = await ctx.mcp.list({ location: { directory } })
        const servers: ListedServer[] = [...(listed.data ?? [])]
        const now = Date.now()
        const due: string[] = []
        for (const server of servers) {
          // Only a healthy server clears the backoff. A reconnect cycle moves
          // the status through `pending`, and clearing on that would reset the
          // counter on every attempt and hammer a server that is genuinely down.
          if (server.status?.status === "connected") {
            attempts.delete(server.name)
            dueAt.delete(server.name)
            continue
          }
          if (server.status?.status !== "failed") continue
          const at = dueAt.get(server.name) ?? now
          if (at > now) {
            delay = Math.min(delay, at - now)
            continue
          }
          due.push(server.name)
        }
        for (const name of [...attempts.keys()]) {
          if (!servers.some((server) => server.name === name)) {
            attempts.delete(name)
            dueAt.delete(name)
          }
        }
        for (const name of due) {
          if (!(await claimAttempt())) {
            delay = Math.min(delay, ATTEMPT_FLOOR_MS)
            continue
          }
          try {
            await reconnect(name)
          } catch {
            // The next check reads the status again.
          }
          const count = (attempts.get(name) ?? 0) + 1
          // Doubling from 1 s to a 30 s ceiling for the first ten attempts,
          // which covers any network blip; a server that is genuinely broken
          // backs off to one attempt every 5 minutes.
          const wait =
            count > FAST_ATTEMPTS ? SLOW_RETRY_MS : Math.min(INITIAL_RETRY_MS * 2 ** (count - 1), MAX_RETRY_MS)
          attempts.set(name, count)
          dueAt.set(name, Date.now() + wait)
          delay = Math.min(delay, wait)
        }
      } catch {
        // The status is unavailable while the service shuts down or reloads;
        // the idle check picks up again when it is back.
      } finally {
        running = false
        const wake = wakeRequested
        wakeRequested = false
        schedule(wake ? INITIAL_RETRY_MS : delay)
      }
    }

    const controller = new AbortController()
    void (async () => {
      try {
        for await (const event of ctx.event.subscribe({ signal: controller.signal })) {
          if (event.type === "mcp.status.changed") wake()
        }
      } catch {
        // The subscription ends with the plugin.
      }
    })()

    schedule(INITIAL_RETRY_MS)

    return () => {
      disposed = true
      controller.abort()
      if (timer !== undefined) clearTimeout(timer)
    }
  },
})
