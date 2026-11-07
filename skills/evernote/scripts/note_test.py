#!/usr/bin/env python3
"""Test a note build by deepseek in opencode, reproducibly, and report which provider and model did the work.

    python3 note_test.py --brief brief.md --out <folder> [--session ses_...] [--cwd ~/Software/Prototypes/socrates]

The run is the installed path: `opencode run --standalone --agent socrates` with the brief as the message, so
the agent reads the evernote skill and drives note_build.py itself. Providers, in order: the OpenCode Go API
(opencode-go/deepseek-v4.1-flash#high), then the direct DeepSeek API (deepseek/deepseek-flash#high). A provider
error (spent quota, model unavailable, cut connection) moves the same session to the next provider at once.

Quick abandon (RULES.md rule 74): the run stops when two `note_build.py next` rounds in a row lower neither the
failure count nor change the first failure, when no event arrives for --idle seconds, or past --budget seconds.

Writes <out>/report.md (providers used, rounds, costs, outcome) and <out>/events.jsonl, and prints one line per
event worth acting on, so a Monitor can follow it. Exit: 0 written and verified, 3 the agent asks Chaehan,
4 stuck, 5 idle or over budget, 6 every provider failed, 1 otherwise.
"""
from __future__ import annotations

import argparse
import json
import os
import queue
import re
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

PROVIDERS = ["opencode-go/deepseek-v4.1-flash#high", "deepseek/deepseek-flash#high"]
PROVIDER_ERROR = re.compile(r"quota|usage limit|unavailable|rate.?limit|\b429\b|\b5\d\d\b|ECONNRESET|socket|"
                            r"overloaded|provider\.", re.I)
SOCRATES = Path.home() / "Software" / "Prototypes" / "socrates"
SUBS = ("init", "next", "write", "verify", "link", "extract")


def classify_next(out: str) -> tuple[str, list[str]]:
    """What one `next` printed: pass, ask, fix (with its failure lines), step, or other."""
    if "PASS. The note text is stamped" in out:
        return "pass", []
    if "Ask Chaehan" in out:
        return "ask", [l for l in out.splitlines() if l.startswith("- ")]
    if re.search(r"^(?:Fix |The gate fails|These sections keep none)", out, re.M):
        return "fix", [l for l in out.splitlines() if l.startswith("- ")]
    if re.search(r"Step \d of 3", out):
        return "step", []
    return "other", []


def _norm(line: str) -> str:
    return re.sub(r"\d+", "#", line)[:120]


class Rounds:
    """The `next` rounds of one build, and the stuck test of rule 74."""

    def __init__(self) -> None:
        self.fixes: list[list[str]] = []  # consecutive fix rounds since the last progress
        self.log: list[tuple[float, str, int, str]] = []

    def add(self, t: float, kind: str, lines: list[str]) -> None:
        self.log.append((t, kind, len(lines), lines[0] if lines else ""))
        if kind == "fix":
            self.fixes.append(lines)
        else:
            self.fixes = []

    def stuck(self) -> list[str] | None:
        """The repeated failure, when the last three fix rounds hold or raise the count on the same first failure."""
        if len(self.fixes) < 3:
            return None
        a, b, c = self.fixes[-3:]
        if len(a) <= len(b) <= len(c) and a and _norm(a[0]) == _norm(b[0]) == _norm(c[0]):
            return c
        return None


class Run:
    def __init__(self, args) -> None:
        self.a = args
        self.out = Path(args.out).resolve()
        self.out.mkdir(parents=True, exist_ok=True)
        self.events = (self.out / "events.jsonl").open("a", encoding="utf-8")
        self.session = args.session
        self.rounds = Rounds()
        self.segments: list[dict] = []
        self.tools: list[tuple[float, str, str]] = []
        self.last_text = ""
        self.written = self.verified = False
        self.t0 = time.time()

    def say(self, line: str) -> None:
        print(f"{time.strftime('%H:%M:%S')} {line}", flush=True)

    def launch(self, model: str, message: str) -> subprocess.Popen:
        cmd = ["opencode", "run", "--standalone", "--agent", self.a.agent, "-m", model, "--format", "json",
               "--title", self.a.title]
        if self.session:
            cmd += ["--session", self.session]
        # opencode takes its project from $PWD, which a child inherits from the launching shell, not from
        # its working directory: launched from agentkit, it looked for the agent there and answered
        # 'Agent not found: "socrates"' (2026-11-07, hanji_test.py).
        env = dict(os.environ, NOTE_BUILD_SOCRATES=str(self.a.cwd), PWD=str(self.a.cwd))
        err = (self.out / "opencode.stderr").open("a")
        return subprocess.Popen(cmd + [message], cwd=self.a.cwd, env=env, stdout=subprocess.PIPE, stderr=err,
                                text=True, start_new_session=True)

    @staticmethod
    def stop(p: subprocess.Popen) -> None:
        if p.poll() is not None:
            return
        try:
            os.killpg(p.pid, signal.SIGTERM)
            p.wait(5)
        except Exception:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except Exception:
                pass

    def segment(self, model: str, message: str) -> str:
        """Run one provider until the agent ends its turn; return why it ended."""
        seg = {"model": model, "start": time.time(), "steps": 0, "cost": 0.0, "tokens": 0, "end": None, "why": ""}
        self.segments.append(seg)
        self.say(f"PROVIDER {model}" + (f" (session {self.session})" if self.session else ""))
        p = self.launch(model, message)
        q: queue.Queue = queue.Queue()
        threading.Thread(target=lambda: [q.put(l) for l in p.stdout] + [q.put(None)], daemon=True).start()
        last = time.time()
        why = ""
        while True:
            try:
                line = q.get(timeout=5)
            except queue.Empty:
                if time.time() - last > self.a.idle:
                    why = f"idle {self.a.idle} s"
                elif time.time() - self.t0 > self.a.budget:
                    why = f"over the {self.a.budget} s budget"
                if why:
                    break
                continue
            if line is None:
                why = "turn ended"
                break
            last = time.time()
            try:
                e = json.loads(line)
            except ValueError:
                continue
            self.events.write(json.dumps({"t": round(last - self.t0, 1), "model": model, **e}, ensure_ascii=False) + "\n")
            self.session = self.session or e.get("sessionID")
            why = self.event(e, seg)
            if why:
                break
        self.stop(p)
        seg["end"], seg["why"] = time.time(), why
        return why

    def event(self, e: dict, seg: dict) -> str:
        part = e.get("part") or {}
        st = part.get("state") or {}
        if e.get("type") == "error":
            err = json.dumps(e.get("error"), ensure_ascii=False)
            self.say(f"ERROR {err[:240]}")
            return "provider error" if PROVIDER_ERROR.search(err) else "error"
        if e.get("type") == "step_finish":
            seg["steps"] += 1
            seg["cost"] += float(part.get("cost") or 0)
            tok = part.get("tokens") or {}
            seg["tokens"] += int(tok.get("input") or 0) + int(tok.get("output") or 0) + int(tok.get("reasoning") or 0)
        if e.get("type") == "text" and part.get("text"):
            self.last_text = part["text"]
        if part.get("type") == "tool" and st.get("status") in ("completed", "error"):
            cmd = (st.get("input") or {}).get("command", "") or ""
            out = st.get("output") or st.get("error") or ""
            if "note_build.py" not in cmd:
                return ""
            sub = next((s for s in SUBS if re.search(rf"note_build\.py\s+{s}\b", cmd)), "?")
            first = " / ".join(l for l in out.strip().splitlines()[:2])[:200]
            self.tools.append((time.time() - self.t0, sub, first))
            if sub == "next":
                kind, lines = classify_next(out)
                self.rounds.add(time.time() - self.t0, kind, lines)
                self.say(f"next #{len(self.rounds.log)} {kind} {len(lines) or ''} | {(lines[0] if lines else first)[:160]}")
                if self.rounds.stuck():
                    return "stuck"
            else:
                self.say(f"{sub} | {first}")
            if sub == "write" and re.search(r'"(?:updated|created)":\s*true|"guid":', out) and "PASS" in out:
                self.written = self.verified = True
            if sub == "verify" and "PASS" in out:
                self.verified = True
        return ""

    def go(self) -> int:
        message = Path(self.a.brief).read_text(encoding="utf-8").strip()
        providers = PROVIDERS[PROVIDERS.index(self.a.start):] if self.a.start in PROVIDERS else PROVIDERS
        code, why = 6, ""
        for i, model in enumerate(providers):
            first = message if not self.session else (message if i == 0 else
                                                      "Continue the task where you stopped, as the first message says.")
            why = self.segment(model, first)
            seg = self.segments[-1]
            if why == "error" and seg["steps"] == 0 and seg["end"] - seg["start"] < 15:
                # A launch that fails before its first step ("Agent not found" while another
                # standalone server shuts down, 2026-11-07) is retried once on the same provider.
                time.sleep(20)  # the 2026-11-07 window lasted ~60 s; two retries 3 s apart both failed
                why = self.segment(model, first)
            if why == "provider error" or (why.startswith("idle") and self.segments[-1]["steps"] == 0):
                # A provider that never takes a step (silent for --idle seconds, 2026-11-07) counts as failed.
                why = "provider error" if why.startswith("idle") else why
                continue
            break
        self.check_build()
        last_kind = self.rounds.log[-1][1] if self.rounds.log else ""
        if why == "provider error":
            code = 6
        elif why == "stuck":
            code = 4
        elif why.startswith(("idle", "over")):
            code = 5
        elif self.written and self.verified:
            code = 0
        elif last_kind == "ask":
            code = 3
        else:
            code = 1
        self.report(code, why)
        self.say(f"DONE exit {code} ({why}); report {self.out / 'report.md'}")
        return code

    def check_build(self) -> None:
        """Read the outcome from the build folder: opencode can move a slow write out of the event stream."""
        if not self.a.build:
            return
        back = Path(self.a.build) / "readback.md"
        if back.exists() and back.stat().st_mtime > self.t0:
            self.written = True
            r = subprocess.run([sys.executable, str(Path(__file__).with_name("note_build.py")), "verify",
                                self.a.build, str(back)], capture_output=True, text=True,
                               env=dict(os.environ, NOTE_BUILD_SOCRATES=str(self.a.cwd)))
            self.verified = r.returncode == 0
            self.say(f"build folder: written, verify {'PASS' if self.verified else 'FAIL: ' + r.stdout[-200:]}")

    def report(self, code: int, why: str) -> None:
        hm = lambda t: time.strftime("%H:%M:%S", time.localtime(t))
        lines = [f"# Note build test, {time.strftime('%Y-%m-%d %H:%M')}", "",
                 f"Outcome: exit {code}, {why}; written {self.written}, verified {self.verified}; "
                 f"{time.time() - self.t0:.0f} s wall; session {self.session}.", "",
                 f"Brief: {Path(self.a.brief).resolve()}; project folder {self.a.cwd}; agent {self.a.agent}.", "",
                 "## Providers used", "", "| Model | Start | End | Steps | Tokens | Cost USD | Ended because |",
                 "| --- | --- | --- | --- | --- | --- | --- |"]
        lines += [f"| {s['model']} | {hm(s['start'])} | {hm(s['end'] or time.time())} | {s['steps']} | {s['tokens']} | "
                  f"{s['cost']:.4f} | {s['why']} |" for s in self.segments]
        lines += ["", "## note_build calls", "", "| t (s) | Command | Kind | Failures | First line |",
                  "| --- | --- | --- | --- | --- |"]
        rounds = iter(self.rounds.log)
        for t, sub, first in self.tools:
            if sub == "next":
                _, kind, n, f = next(rounds)
                lines.append(f"| {t:.0f} | next | {kind} | {n} | {(f or first)[:110].replace('|', '/')} |")
            else:
                lines.append(f"| {t:.0f} | {sub} | | | {first[:110].replace('|', '/')} |")
        stuck = self.rounds.stuck()
        if stuck:
            lines += ["", "## Stuck on", ""] + stuck
        lines += ["", "## The agent's last message", "", self.last_text.strip() or "(none)", ""]
        (self.out / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--brief", required=True, help="the message the agent gets, as a file")
    ap.add_argument("--out", required=True, help="folder for report.md and events.jsonl")
    ap.add_argument("--session", help="continue this opencode session, e.g. with Chaehan's answers as the brief")
    ap.add_argument("--cwd", default=str(SOCRATES), help="the project folder the agent runs in")
    ap.add_argument("--build", help="the note_build folder the brief names; its read-back decides written and verified")
    ap.add_argument("--agent", default="socrates")
    ap.add_argument("--title", default="note build test")
    ap.add_argument("--start", default=PROVIDERS[0], help="first provider to try")
    ap.add_argument("--idle", type=int, default=300, help="seconds without an event before the run stops")
    ap.add_argument("--budget", type=int, default=1500, help="seconds the whole run may take")
    return Run(ap.parse_args(argv)).go()


if __name__ == "__main__":
    sys.exit(main())
