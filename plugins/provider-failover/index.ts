// provider-failover — a session that keeps losing its socket to the opencode.ai
// gateway finishes its turn on the direct DeepSeek API instead, and goes back to
// the gateway afterwards.
//
// Why this exists (measured 2026-10-20 over ~25.8k assistant messages in
// ~/.local/share/opencode/opencode.db): 42 assistant messages ended with
// `provider.transport` ECONNRESET, spread over 26 sessions, 2026-09-26 to
// 2026-10-20. Every one of them was `opencode-go` / `deepseek-v4.1-flash`; the
// direct `deepseek` provider never reset in 754 calls and the other gateway
// models never reset in 197. The failing calls are long ones (mean 304 s vs
// 60 s) on deep prompts (median ~180k tokens), which is the band where the
// gateway routes the same model to upstreams with different context limits
// (anomalyco/opencode#50761) and drops the stream (anomalyco/opencode#57033).
//
// OpenCode's own retry is per session and stays on the same route: 2 s, 4 s,
// then 10 s gaps, ten times, ~84 s before the turn ends as an error
// (packages/core/src/session/runner/retry.ts). Four failed attempts is 2 + 4 +
// 8 = ~14 s of that budget — long enough that a blip recovers by itself, short
// enough that a dead route costs a quarter minute instead of a quarter hour.
//
// The model switch takes effect on the next attempt, not the current one: on a
// retry the runner calls prepareContext → context.select again
// (packages/core/src/session/runner/llm.ts), which re-reads the session's model.
//
// The fallback model is `deepseek-flash` on the direct provider, which is the
// same model: api.deepseek.com/models returns it as "DeepSeek-V4.1-Flash",
// 1048576 context, effort low/high/max (checked 2026-10-20). The session's own
// effort variant is carried over.
//
// Going back is remembered, not left to the next restart: the turn's original
// model ref is written to plugin storage the moment the switch happens, and the
// session is switched back when the turn ends (session.idle) or, if the app died
// first, on the next prompt of that session or on the next plugin setup. A
// restore only touches a session whose model is still the fallback, so a model
// the user picks during the fallback turn is never overwritten.

import { Plugin } from "@opencode/plugin"
import { appendFileSync } from "node:fs"
import { homedir } from "node:os"
import { join } from "node:path"

const PRIMARY_PROVIDER = "opencode-go"
const PRIMARY_MODEL = "deepseek-v4.1-flash"
const FALLBACK_PROVIDER = "deepseek"
const FALLBACK_MODEL = "deepseek-flash"

/** Consecutive connection failures in one session before the session moves. */
export const FALLBACK_AFTER = 4
/** Retry gaps the runner waits before attempts 2, 3 and 4 (retry.ts schedule). */
export const RETRY_GAPS_MS = [2_000, 4_000, 8_000]
/** Wait before the attempt that runs on the fallback model. */
const SWITCH_DELAY_MS = 1_000

const STORAGE_PREFIX = "agentkit.provider-failover:"
const LOG_PATH = join(homedir(), ".local/share/opencode/log/provider-failover.log")

// The class that actually ends sessions. A header or chunk timeout is a
// different failure — it already carries its own attempt ceiling in the runner —
// and must not move the session off the gateway.
const CONNECTION_FAILURE =
  /ECONNRESET|ECONNREFUSED|socket connection was closed|other side closed|fetch failed|connection refused|network connection lost/i

export type ModelRef = { providerID: string; id: string; variant?: string }

export const isConnectionFailure = (error: { type?: string; message?: string } | undefined): boolean =>
  error?.type === "provider.transport" && CONNECTION_FAILURE.test(error.message ?? "")

/** Milliseconds of retry waiting burned by `attempts` failed attempts. */
export const waitedFor = (attempts: number): number =>
  RETRY_GAPS_MS.slice(0, Math.max(0, attempts - 1)).reduce((sum, ms) => sum + ms, 0)

/** A restore must not overwrite a model the user chose during the fallback turn. */
export const stillOnFallback = (model: ModelRef | undefined): boolean =>
  model?.providerID === FALLBACK_PROVIDER && model.id === FALLBACK_MODEL

type Failover = { from: ModelRef; at: number }

const message = (error: unknown) => (error instanceof Error ? error.message : String(error))

export default Plugin.define({
  id: "agentkit.provider-failover",
  async setup(ctx) {
    const failures = new Map<string, number>()
    const switched = new Map<string, Failover>()
    const stop = new AbortController()

    const log = (line: string) => {
      try {
        appendFileSync(LOG_PATH, `${new Date().toISOString()} ${line}\n`)
      } catch {
        // a log failure must never break a retry
      }
    }

    const key = (sessionID: string) => `${STORAGE_PREFIX}${sessionID}`

    log(`loaded v${ctx.app?.version ?? "?"} ${ctx.location?.directory ?? ""}`)

    const forget = async (sessionID: string) => {
      switched.delete(sessionID)
      failures.delete(sessionID)
      await ctx.storage.remove(key(sessionID)).catch(() => undefined)
    }

    const restore = async (sessionID: string) => {
      const record = switched.get(sessionID) ?? ((await ctx.storage.get(key(sessionID)).catch(() => undefined)) as Failover | undefined)
      if (!record?.from) return
      const info = await ctx.session.get({ sessionID }).catch(() => undefined)
      if (!stillOnFallback(info?.model)) {
        log(`restore skipped ${sessionID}: model is ${info?.model?.providerID}/${info?.model?.id}`)
        await forget(sessionID)
        return
      }
      await forget(sessionID)
      try {
        await ctx.session.switchModel({ sessionID, model: record.from })
        log(`restored ${sessionID} to ${record.from.providerID}/${record.from.id}${record.from.variant ? "#" + record.from.variant : ""}`)
      } catch (error) {
        log(`restore failed ${sessionID}: ${message(error)}`)
      }
    }

    const failover = async (sessionID: string, from: ModelRef): Promise<boolean> => {
      const record: Failover = { from: { providerID: from.providerID, id: from.id, variant: from.variant }, at: Date.now() }
      // Stored before the switch: if the switch succeeds and the app dies before
      // the turn ends, setup finds the record and puts the session back.
      await ctx.storage.set(key(sessionID), record).catch(() => undefined)
      switched.set(sessionID, record)
      try {
        await ctx.session.switchModel({ sessionID, model: { providerID: FALLBACK_PROVIDER, id: FALLBACK_MODEL, variant: from.variant } })
        log(`switched ${sessionID} to ${FALLBACK_PROVIDER}/${FALLBACK_MODEL} after ${FALLBACK_AFTER} resets`)
        return true
      } catch (error) {
        log(`switch failed ${sessionID}: ${message(error)}`)
        await forget(sessionID)
        return false
      }
    }

    await ctx.session.hook(
      "retry",
      async (input) => {
        try {
          const model = input.model as unknown as ModelRef
          if (model.providerID !== PRIMARY_PROVIDER || model.id !== PRIMARY_MODEL) return
          if (switched.has(input.sessionID)) return
          if (!isConnectionFailure(input.error)) return
          const count = (failures.get(input.sessionID) ?? 0) + 1
          failures.set(input.sessionID, count)
          log(`reset ${input.sessionID} attempt=${input.attempt} consecutive=${count} ${(input.error.message ?? "").slice(0, 160)}`)
          if (count < FALLBACK_AFTER) return
          if (await failover(input.sessionID, model)) input.decision = { retry: true, delay: SWITCH_DELAY_MS }
        } catch (error) {
          log(`retry hook failed: ${message(error)}`)
        }
      },
      { providerID: PRIMARY_PROVIDER },
    )

    // The next typed message is the point where the session is meant to be back
    // on the gateway. A steer is not: it lands inside the turn the fallback is
    // still carrying.
    await ctx.session.hook("prompt", async (input) => {
      try {
        const delivery = (input as { delivery?: { type?: string } | string }).delivery
        const type = typeof delivery === "string" ? delivery : delivery?.type
        if (type === "steer") return
        if (switched.has(input.sessionID) || (await ctx.storage.get(key(input.sessionID)).catch(() => undefined))) await restore(input.sessionID)
      } catch (error) {
        log(`prompt hook failed: ${message(error)}`)
      }
    })

    void (async () => {
      try {
        for await (const event of ctx.event.subscribe({ signal: stop.signal })) {
          try {
            if (event.type !== "session.idle") continue
            const sessionID = (event as { data?: { sessionID?: string } }).data?.sessionID
            if (sessionID && (switched.has(sessionID) || (await ctx.storage.get(key(sessionID)).catch(() => undefined))))
              await restore(sessionID)
          } catch (error) {
            log(`idle handler failed: ${message(error)}`)
          }
        }
      } catch (error) {
        log(`event stream ended: ${message(error)}`)
      }
    })()

    // A location reload can leave a session on the fallback from a previous
    // process (crash, quit during a failed turn). Put those back now.
    try {
      const { entries } = await ctx.storage.scan({ prefix: STORAGE_PREFIX })
      for (const entry of entries) await restore(entry.key.slice(STORAGE_PREFIX.length))
    } catch (error) {
      log(`setup restore failed: ${message(error)}`)
    }

    return () => {
      stop.abort()
    }
  },
})
