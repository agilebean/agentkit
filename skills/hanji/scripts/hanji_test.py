#!/usr/bin/env python3
"""Test the hanji skill (or the Evernote MCP) with deepseek in opencode, and time every tool call.

    python3 hanji_test.py --brief brief.md --out <folder> [--session ses_...]

The run is the installed path, as in the evernote skill's note_test.py, whose launch, provider
fallback (the OpenCode Go API first, then the direct DeepSeek API) and idle and budget stops it
reuses: `opencode run --standalone --agent socrates` in the socrates folder with the brief as the
message. Writes <out>/report.md (providers, steps, tokens, cost, and one row per hanji command with
its duration, exit and first output line) and <out>/events.jsonl. Exit 0 when every helper write
the agent ran verified and none failed, 1 otherwise, 5 idle or over budget, 6 every provider failed.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import time
from pathlib import Path

_nt = Path(__file__).resolve().parents[2] / "evernote" / "scripts" / "note_test.py"
_spec = importlib.util.spec_from_file_location("note_test", _nt)
note_test = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(note_test)

HELPER = re.compile(r"(?:hanji_note\.py|\$P)\s+(?:--db\s+\S+\s+)?([a-z][a-z-]+)")
RAW = re.compile(r"(?:MacOS/hanji|\$H|\bhanji)\s+(?:--json\s+)?(?:--db\s+\S+\s+)?(?:--json\s+)?([a-z]+(?:\s+[a-z-]+)?)")


class HanjiRun(note_test.Run):
    def __init__(self, args) -> None:
        super().__init__(args)
        self.calls: list[dict] = []

    def event(self, e: dict, seg: dict) -> str:
        part = e.get("part") or {}
        st = part.get("state") or {}
        if part.get("type") == "tool" and st.get("status") in ("completed", "error"):
            inp = st.get("input") or {}
            cmd = str(inp.get("command") or inp.get("code") or inp.get("name") or "")
            out = str(st.get("output") or st.get("error") or "")
            t = st.get("time") or {}
            ms = (t.get("end", 0) - t.get("start", 0)) if t.get("start") else None
            ex = ((st.get("metadata") or {}).get("metadata") or {}).get("exit")
            subs = HELPER.findall(cmd) or [f"hanji {m}" for m in RAW.findall(cmd)]
            what = " + ".join(dict.fromkeys(subs)) if subs else part.get("tool", "?")
            row = {"t": round(time.time() - self.t0), "tool": part.get("tool"), "what": what, "ms": ms,
                   "exit": ex, "status": st.get("status"), "verified": out.count('"verified": true'),
                   "failed": st.get("status") == "error" or (ex not in (None, 0, 3)),  # 3 is "not found", an answer
                   "first": " / ".join(out.strip().splitlines()[:2])[:160], "command": cmd[:600]}
            self.calls.append(row)
            self.say(f"{row['tool']} {what[:60]} {ms} ms exit {ex}{' verified x' + str(row['verified']) if row['verified'] else ''} | {row['first'][:100]}")
        # provider errors, steps, tokens and the last text are counted by note_test's own handler
        if part.get("type") == "tool":
            return ""
        return super().event(e, seg)

    def check_build(self) -> None:
        """Written and verified come from the helper's own output, not a build folder."""
        self.written = any(c["verified"] for c in self.calls)
        self.verified = self.written and not any(c["failed"] for c in self.calls)

    def report(self, code: int, why: str) -> None:
        super().report(code, why)
        p = self.out / "report.md"
        text = p.read_text(encoding="utf-8").replace("# Note build test", "# Hanji skill test", 1)
        head, _, tail = text.partition("## note_build calls")
        _, _, last = tail.partition("## The agent's last message")
        rows = ["## Tool calls", "",
                "Duration is opencode's own start-to-end time of the shell call, which may hold more than one command.", "",
                "| t (s) | Tool | Commands | ms | Exit | Verified writes | First output line |",
                "| --- | --- | --- | --- | --- | --- | --- |"]
        rows += [f"| {c['t']} | {c['tool']} | {c['what'][:60]} | {c['ms']} | {c['exit'] if c['exit'] is not None else ''} | "
                 f"{c['verified'] or ''} | {c['first'][:100].replace('|', '/')} |" for c in self.calls]
        p.write_text(head + "\n".join(rows) + "\n\n## The agent's last message" + last, encoding="utf-8")
        (self.out / "calls.json").write_text(json.dumps(self.calls, ensure_ascii=False, indent=1), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--brief", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--session")
    ap.add_argument("--cwd", default=str(note_test.SOCRATES))
    ap.add_argument("--agent", default="socrates")
    ap.add_argument("--title", default="hanji skill test")
    ap.add_argument("--start", default=note_test.PROVIDERS[0])
    ap.add_argument("--idle", type=int, default=300)
    ap.add_argument("--budget", type=int, default=1200)
    a = ap.parse_args(argv)
    a.build = None
    return HanjiRun(a).go()


if __name__ == "__main__":
    sys.exit(main())
