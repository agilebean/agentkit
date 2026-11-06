import { expect, test } from "bun:test"
import { mkdtempSync, utimesSync, writeFileSync } from "node:fs"
import { tmpdir } from "node:os"
import { join } from "node:path"
import plugin, { MESSAGE } from "./index.ts"

const SHA = "8841e5e77c030090a9e033ee40d5c674fd9c95a4ee15d6e57dc5e763baa4c70f"

async function hook() {
  let fn: (e: any) => unknown = () => {}
  const ctx: any = { tool: { hook: async (_name: string, f: any) => { fn = f } } }
  await (plugin as any).setup(ctx)
  return (code: string) => fn({ tool: "execute", input: { code } })
}

function stamps(age_ms = 0) {
  const d = mkdtempSync(join(tmpdir(), "note-gate-"))
  const f = join(d, SHA)
  writeFileSync(f, "")
  const t = (Date.now() - age_ms) / 1000
  utimesSync(f, t, t)
  process.env.NOTE_GATE_STAMPS = d
}

const CREATE = `await tools.evernote.create_note({ title: "2026-11-06 X", content: "<div>x</div>" })`
const REPLACE = `await tools.evernote.edit_note({ noteId: "g", mode: "replace", find: "<h2>a</h2></en-note>", content: "b" })`
const CELL = `await tools.evernote.edit_note({ noteId: "g", mode: "replace", find: "2:05", content: "2:04" })`

test("a new note or a whole-body replace without a marker is refused", async () => {
  stamps()
  const call = await hook()
  expect(() => call(CREATE)).toThrow(MESSAGE)
  expect(() => call(REPLACE)).toThrow(MESSAGE)
})

test("a surgical edit and a read are left alone", async () => {
  stamps()
  const call = await hook()
  expect(() => call(CELL)).not.toThrow()
  expect(() => call(`await tools.evernote.get_note({ noteId: "g" })`)).not.toThrow()
})

test("a live marker lets the write through and a stale one does not", async () => {
  stamps()
  let call = await hook()
  expect(() => call(`// note-gate:${SHA}\n` + CREATE)).not.toThrow()
  stamps(4 * 60 * 60 * 1000)
  call = await hook()
  expect(() => call(`// note-gate:${SHA}\n` + CREATE)).toThrow(MESSAGE)
})

test("the shell tool is not this plugin's", async () => {
  stamps()
  let fn: (e: any) => unknown = () => {}
  await (plugin as any).setup({ tool: { hook: async (_n: string, f: any) => { fn = f } } })
  expect(() => fn({ tool: "shell", input: { command: CREATE } })).not.toThrow()
})
