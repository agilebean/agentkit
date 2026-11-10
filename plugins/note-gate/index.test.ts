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

// The shape of the 2026-11-08 section rewrites (failure 201): a find/replace
// under 6000 characters whose content is a paragraph of prose.
const SECTION = "await tools.evernote.edit_note({ noteId: \"g\", mode: \"replace\", find: `<div><strong>Where it is</strong></div>`, " +
  "content: `<div><strong>Where it is</strong></div><div>The pain sits at the front of the right shoulder, lateral to the long head " +
  "of biceps. From lateral to medial you feel five structures: the deltoid, the greater tuberosity, the long head of biceps, the short " +
  "head of biceps, and the pec major.</div>` })"
const SENTENCE = `await tools.evernote.edit_note({ noteId: "g", mode: "replace", find: "a very small hump", content: "the greater tuberosity, a small bony hump" })`
const ROW = "await tools.evernote.edit_note({ noteId: \"g\", mode: \"replace\", find: `<tr><td><div>2026-11-03</div></td></tr>`, " +
  "content: `<tr><td><div>2026-11-03</div></td><td><div>6x100 m at 60, 70 and 80 percent twice, 3x50 m at 90 percent, the classic " +
  "set, with the new catch from stretched out to a very small elbow flex and no bursa pain afterwards, 1050 m in all</div></td></tr>` })"

test("a section rewritten through a small edit is a body write", async () => {
  stamps()
  const call = await hook()
  expect(() => call(SECTION)).toThrow(MESSAGE)
  expect(() => call(`// note-gate:${SHA}\n` + SECTION)).not.toThrow()
})

test("one sentence and a table row stay surgical", async () => {
  stamps()
  const call = await hook()
  expect(() => call(SENTENCE)).not.toThrow()
  expect(() => call(ROW)).not.toThrow()
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

test("a stamp in the fallback folder a sandboxed gate writes is read", async () => {
  const home = mkdtempSync(join(tmpdir(), "note-gate-home-"))
  const dir = join(home, ".cache/agentkit/note-gate")
  require("node:fs").mkdirSync(dir, { recursive: true })
  writeFileSync(join(dir, SHA), "")
  const old = { home: process.env.HOME, stamps: process.env.NOTE_GATE_STAMPS }
  process.env.HOME = home
  delete process.env.NOTE_GATE_STAMPS
  try {
    const call = await hook()
    expect(() => call(`// note-gate:${SHA}\n` + CREATE)).not.toThrow()
    expect(() => call(`// note-gate:${"0".repeat(64)}\n` + CREATE)).toThrow(MESSAGE)
  } finally {
    process.env.HOME = old.home
    if (old.stamps) process.env.NOTE_GATE_STAMPS = old.stamps
  }
})
