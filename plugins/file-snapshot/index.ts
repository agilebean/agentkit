// file-snapshot - keeps a copy of an important file before an agent changes it.
//
// opencode's own snapshot ran a git add of the whole repo the run started in, on
// every step. It cost 1 to 3 s per tool call (rule 74, measured 2026-11-14) and it
// never reached the files that matter most: the KUBS grading documents and the
// lecture decks sit on Drive, outside every repo, so its stores held only socrates
// files that git already versions. It is off since 2026-11-15 ("snapshot": false
// in ~/.config/opencode/opencode.jsonc). Chaehan, 2026-11-15: "can you apply a
// heuristic to snapshots are taken for important files, like grading or lecture
// slides."
//
// The heuristic: a file is important when it sits under one of RULES' folders and
// has one of its extensions (the documents and decks, never the recordings,
// renders or submitted PDFs). Before a write or edit of such a file, and before a
// shell command that names its folder and changes something, the file is copied
// to ~/.local/share/agentkit/snapshots/<path under the root>/<time>.<ext>.
// A version already copied (same size and modification time) is not copied
// again, and the newest KEEP versions of each file are kept. The copy is an APFS
// clone where the volume allows it, so an 11 MB deck costs no space and a few
// milliseconds. Any error is logged and never stops the tool call.
//
// Restore: cp the version you want back over the file (index.tsv beside the
// versions says when and by which tool call each one was taken).

import { Plugin } from "@opencode/plugin"
import {
  appendFileSync, constants, copyFileSync, existsSync, mkdirSync, readdirSync, readFileSync, rmSync, statSync,
} from "node:fs"
import { homedir } from "node:os"
import { basename, dirname, extname, join } from "node:path"

const home = () => process.env.HOME || homedir()

export const KEEP = 10

// Each rule: a folder (found by this path fragment, so no account name is written
// here) and the extensions that are documents in it.
export const RULES: Array<{ name: string; under: string; ext: string[] }> = [
  { name: "KUBS DT grading and lecture slides", under: "/My Drive/1 Projects/KUBS/KUBS DT/",
    ext: [".key", ".md", ".csv", ".tsv", ".xlsx", ".numbers", ".json", ".pptx"] },
]

export function snapshotDir(): string {
  return process.env.FILE_SNAPSHOT_DIR || join(home(), ".local/share/agentkit/snapshots")
}

// The rule a path falls under and the path below its folder, or null.
export function important(path: string): { rule: (typeof RULES)[number]; rel: string } | null {
  for (const rule of RULES) {
    const i = path.indexOf(rule.under)
    if (i < 0) continue
    if (!rule.ext.includes(extname(path).toLowerCase())) return null
    return { rule, rel: path.slice(i + rule.under.length) }
  }
  return null
}

// The absolute folder of each rule on this machine: from $FILE_SNAPSHOT_ROOT, or
// the Drive folders under ~/Library/CloudStorage.
export function roots(): string[] {
  if (process.env.FILE_SNAPSHOT_ROOT) return [process.env.FILE_SNAPSHOT_ROOT]
  const cloud = join(home(), "Library/CloudStorage")
  const out: string[] = []
  try {
    for (const d of readdirSync(cloud)) {
      for (const rule of RULES) {
        const r = join(cloud, d, rule.under)
        if (existsSync(r)) out.push(r)
      }
    }
  } catch {}
  return out
}

// A shell command changes files when it copies, moves, deletes, redirects into a
// file, edits in place or runs a program (a script can write anything it is
// given). `2>&1` and `> /dev/null` write no file: on 2026-11-15 an `ls ... 2>&1`
// of the two folders was the call that took the first copies.
const WRITES = /(^|[\s;&|(`])(cp|mv|rm|ditto|rsync|tee|touch|truncate|unzip|zip|python3?|osascript|bun|node|perl|ruby|sh|bash|mamba)\b|\bsed\s+-i|(?<![0-9&>])>>?(?!>|\s*(&|\/dev\/null))/

// The important files a shell command may change: in each rule folder's direct
// subfolders that the command names, the files whose name it names, or all of
// that subfolder's important files when it names none of them.
// Each rule folder's own name ("KUBS DT"): a command that names none of them
// costs one string test and touches no disk.
const MARKERS = RULES.map((r) => r.under.split("/").filter(Boolean).pop() as string)
let cachedRoots: string[] | null = null

export function shellTargets(command: string, rootDirs?: string[]): string[] {
  const cmd = command.replace(/\\ /g, " ")
  if (!MARKERS.some((m) => cmd.includes(m)) || !WRITES.test(cmd)) return []
  const out: string[] = []
  for (const root of rootDirs ?? (cachedRoots ??= roots())) {
    let subs: string[]
    try { subs = readdirSync(root) } catch { continue }
    for (const sub of subs) {
      if (!cmd.includes(sub)) continue
      const dir = join(root, sub)
      let files: string[]
      try { if (!statSync(dir).isDirectory()) continue; files = readdirSync(dir) } catch { continue }
      const docs = files.filter((f) => important(join(dir, f)))
      const named = docs.filter((f) => cmd.includes(f))
      for (const f of named.length ? named : docs) out.push(join(dir, f))
    }
  }
  return [...new Set(out)]
}

function stamp(d = new Date()): string {
  const p = (n: number, w = 2) => String(n).padStart(w, "0")
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}${p(d.getMinutes())}${p(d.getSeconds())}.${p(d.getMilliseconds(), 3)}`
}

// Copy one file before it changes. Returns the copy's path, or null when the file
// is not important, does not exist yet, or this version is already kept.
export function snapshot(path: string, why = ""): string | null {
  const hit = important(path)
  if (!hit) return null
  let st
  try { st = statSync(path) } catch { return null }
  if (!st.isFile()) return null
  const dir = join(snapshotDir(), hit.rel)
  const index = join(dir, "index.tsv")
  const sig = `${st.size}\t${Math.floor(st.mtimeMs)}`
  if (existsSync(index)) {
    const lines = readFileSync(index, "utf8").trim().split("\n")
    const last = lines[lines.length - 1]?.split("\t")
    if (last && `${last[2]}\t${last[3]}` === sig) return null
  }
  mkdirSync(dir, { recursive: true })
  const base = stamp()
  let name = base + extname(path)
  for (let n = 1; existsSync(join(dir, name)); n++) name = `${base}-${n}${extname(path)}`
  const dest = join(dir, name)
  copyFileSync(path, dest, constants.COPYFILE_FICLONE)
  appendFileSync(index, `${name}\t${path}\t${sig}\t${why.replace(/[\t\n]/g, " ").slice(0, 200)}\n`)
  const versions = readdirSync(dir).filter((f) => f !== "index.tsv").sort()
  for (const old of versions.slice(0, Math.max(0, versions.length - KEEP))) rmSync(join(dir, old), { force: true })
  return dest
}

function logError(e: unknown, what: string) {
  try {
    mkdirSync(snapshotDir(), { recursive: true })
    appendFileSync(join(snapshotDir(), "errors.log"), `${new Date().toISOString()}\t${what}\t${String(e)}\n`)
  } catch {}
}

// The files one tool call may change.
export function targets(tool: string, input: Record<string, unknown> | undefined): string[] {
  if (!input) return []
  if (tool === "shell" || tool === "bash") return shellTargets(String(input.command ?? ""))
  const p = input.path ?? input.filePath ?? input.file_path
  return typeof p === "string" ? [p] : []
}

export default Plugin.define({
  id: "agentkit.file-snapshot",
  async setup(ctx) {
    await ctx.tool.hook("execute.before", (event) => {
      if (event.tool === "read" || event.tool === "grep" || event.tool === "glob") return
      const input = event.input as Record<string, unknown> | undefined
      try {
        for (const f of targets(event.tool, input)) {
          try { snapshot(f, `${event.tool} ${basename(dirname(f))}`) } catch (e) { logError(e, f) }
        }
      } catch (e) { logError(e, event.tool) }
    })
  },
})
