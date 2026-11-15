import { expect, test } from "bun:test"
import { mkdirSync, mkdtempSync, readdirSync, readFileSync, utimesSync, writeFileSync } from "node:fs"
import { tmpdir } from "node:os"
import { join } from "node:path"
import plugin, { KEEP, important, shellTargets, snapshot } from "./index.ts"

// A Drive tree like the real one: <tmp>/My Drive/1 Projects/KUBS/KUBS DT/...
function drive() {
  const tmp = mkdtempSync(join(tmpdir(), "file-snapshot-"))
  const root = join(tmp, "My Drive/1 Projects/KUBS/KUBS DT")
  const grading = join(root, "KUBS DT Grading")
  const s8 = join(root, "KUBS DT S8")
  mkdirSync(grading, { recursive: true })
  mkdirSync(s8, { recursive: true })
  writeFileSync(join(grading, "KUBS DT gradebook.md"), "| team | grade |\n| A | 4.5 |\n")
  writeFileSync(join(grading, "2026-10-19 KUBS DT S7 Presentations.mp3"), "audio")
  writeFileSync(join(s8, "KUBS DT WS2026 E08.key"), "deck bytes")
  writeFileSync(join(s8, "KUBS DT WS2026 E08.pdf"), "pdf")
  process.env.FILE_SNAPSHOT_DIR = join(tmp, "snapshots")
  process.env.FILE_SNAPSHOT_ROOT = root
  return { tmp, root, grading, s8, snaps: join(tmp, "snapshots") }
}

async function hook() {
  let fn: (e: any) => unknown = () => {}
  const ctx: any = { tool: { hook: async (_name: string, f: any) => { fn = f } } }
  await (plugin as any).setup(ctx)
  return (tool: string, input: any) => fn({ tool, input })
}

test("grading documents and decks are important; recordings, PDFs and other folders are not", () => {
  const d = drive()
  expect(important(join(d.grading, "KUBS DT gradebook.md"))).not.toBeNull()
  expect(important(join(d.s8, "KUBS DT WS2026 E08.key"))?.rel).toBe("KUBS DT S8/KUBS DT WS2026 E08.key")
  expect(important(join(d.grading, "2026-10-19 KUBS DT S7 Presentations.mp3"))).toBeNull()
  expect(important(join(d.s8, "KUBS DT WS2026 E08.pdf"))).toBeNull()
  expect(important("/Users/x/Software/Prototypes/socrates/memory/travel.md")).toBeNull()
})

test("a write to a grading file keeps the version before it, once per version", async () => {
  const d = drive()
  const call = await hook()
  const f = join(d.grading, "KUBS DT gradebook.md")
  call("write", { path: f, content: "new" })
  call("edit", { path: f, oldString: "4.5", newString: "4.0" })
  const dir = join(d.snaps, "KUBS DT Grading/KUBS DT gradebook.md")
  const versions = readdirSync(dir).filter((x) => x !== "index.tsv")
  expect(versions.length).toBe(1)
  expect(readFileSync(join(dir, versions[0]), "utf8")).toContain("| A | 4.5 |")
  writeFileSync(f, "| team | grade |\n| A | 4.0 |\n")
  utimesSync(f, new Date(), new Date(Date.now() + 5000))
  call("edit", { path: f, oldString: "4.0", newString: "3.5" })
  expect(readdirSync(dir).filter((x) => x !== "index.tsv").length).toBe(2)
})

test("a write to any other file takes no copy", async () => {
  const d = drive()
  const call = await hook()
  const other = join(d.tmp, "draft.md")
  writeFileSync(other, "x")
  call("write", { path: other, content: "y" })
  call("write", { path: join(d.grading, "2026-10-19 KUBS DT S7 Presentations.mp3"), content: "y" })
  expect(() => readdirSync(d.snaps)).toThrow()
})

test("a shell command that installs a deck copies that deck, and a read copies nothing", () => {
  const d = drive()
  const install = `cp "$STAGE/E08 build.key" "${d.s8}/KUBS DT WS2026 E08.key"`
  expect(shellTargets(install, [d.root])).toEqual([join(d.s8, "KUBS DT WS2026 E08.key")])
  expect(shellTargets(`ls "${d.s8}"; md5 "${d.s8}/KUBS DT WS2026 E08.key"`, [d.root])).toEqual([])
  expect(shellTargets(`ls -la "${d.s8}" 2>&1 | head; ls "${d.grading}" > /dev/null`, [d.root])).toEqual([])
  expect(shellTargets(`echo x > "${d.grading}/KUBS DT gradebook.md"`, [d.root])).toEqual([join(d.grading, "KUBS DT gradebook.md")])
  const script = `python3 grade_curve.py --folder ~/Drive/KUBS\\ DT/KUBS\\ DT\\ Grading`
  expect(shellTargets(script, [d.root])).toEqual([join(d.grading, "KUBS DT gradebook.md")])
})

test("only the newest versions are kept", () => {
  const d = drive()
  const f = join(d.grading, "KUBS DT gradebook.md")
  for (let i = 0; i < KEEP + 3; i++) {
    writeFileSync(f, `version ${i}`)
    utimesSync(f, new Date(), new Date(Date.now() + i * 1000))
    snapshot(f, "test")
  }
  const dir = join(d.snaps, "KUBS DT Grading/KUBS DT gradebook.md")
  expect(readdirSync(dir).filter((x) => x !== "index.tsv").length).toBe(KEEP)
})
