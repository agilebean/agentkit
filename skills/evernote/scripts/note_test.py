#!/usr/bin/env python3
"""Test a note build by deepseek in opencode, reproducibly, and report which provider and model did the work.

    python3 note_test.py --brief brief.md --out <folder> [--session ses_...] [--cwd ~/Software/Prototypes/socrates]
    python3 note_test.py --write <build folder> --out <folder>

`--write` is the path Claude Code takes to Evernote: it cannot call the Evernote MCP itself, so after
`note_build.py init --as-is` (or a build) printed PASS, this one command has the agent in opencode run the
folder's `write` and its execute call, and the outcome comes from the folder's own read-back and verify.
`--expect <file> ...` judges a run that writes no note (a read, an export) by the files it must leave.

The run is the installed path: `opencode run --agent socrates` with the brief as the message, so the agent reads
the evernote skill and drives note_build.py itself. It runs against a private `opencode serve` this script starts
(class Server), not `--standalone`, so that the server's event stream shows the model reasoning while `opencode run`
prints nothing; a server that fails to start falls back to `--standalone`. Providers, in order: the OpenCode Go API
(opencode-go/deepseek-v4.1-flash#high), then the direct DeepSeek API (deepseek/deepseek-flash#high). A provider
error (spent quota, model unavailable, cut connection) moves the same session to the next provider at once.

Quick abandon (RULES.md rule 74): this script stops the run when two `note_build.py next` rounds in a row lower
neither the failure count nor change the first failure, when neither `opencode run` nor the server's stream shows the model
working for --idle seconds (RULES.md rule 73: 120), or past --budget seconds.

Writes <out>/report.md (providers used, rounds, costs, the longest silences, outcome), <out>/events.jsonl (what
`opencode run` printed) and <out>/server_events.jsonl (the server's stream, deltas as their length), and prints one
line per event worth acting on, so a Monitor can follow it. Exit: 0 written and verified, 3 the agent asks Chaehan,
4 stuck, 5 idle or over budget, 6 every provider failed, 1 otherwise.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import queue
import re
import secrets
import signal
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

PROVIDERS = ["opencode-go/deepseek-v4.1-flash#high", "deepseek/deepseek-flash#high"]
PROVIDER_ERROR = re.compile(r"quota|usage limit|unavailable|rate.?limit|\b429\b|\b5\d\d\b|ECONNRESET|socket|"
                            r"overloaded|provider\.", re.I)
SOCRATES = Path.home() / "Software" / "Prototypes" / "socrates"
SUBS = ("init", "next", "write", "verify", "link", "extract")
# The folder travels in $NOTE_BUILD_WRITE: on 2026-11-10 DeepSeek retyped a 150-character scratch path with two
# letters doubled, and its first write failed on a folder that did not exist.
WRITE_BRIEF = ("Evernote write. Run `python3 {nb} write \"$NOTE_BUILD_WRITE\"` and run the code it prints in ONE "
               "execute call, exactly as printed. The printed code is complete: do not read the script. Change "
               "nothing else, ask nothing, and end with the lines the call returned.")
# Server events that show the model or a tool at work. session.retry.scheduled is left out: a provider that keeps
# failing would otherwise look alive.
LIVE = re.compile(r"^session\.(?:reasoning|text|tool|step|shell|compaction)\.")


class Server:
    """A private `opencode serve` whose event stream shows the model working while `opencode run` is silent.

    `opencode run --format json` prints a part only once it is complete, so a DeepSeek step that reasons for
    minutes prints nothing between step_start and its first tool call. Three life-overview runs were cut that way,
    on 2026-11-17 twice at 120 s and on 2026-11-19 at 300 s, each right after the agent read the skill and the
    sources. The server's /api/event stream sends session.reasoning.delta, session.text.delta and
    session.tool.input.delta while the model streams: measured 2026-11-20 on a 7 s reasoning step, 48 reasoning
    deltas never more than 0.5 s apart, while `opencode run` printed nothing. The server reads its password from
    OPENCODE_SERVER_PASSWORD, and the run client sends the same variable; the agent's shell tool runs inside the
    server, so the server starts with the environment the tools need ($NOTE_BUILD_SOCRATES, $NOTE_BUILD_WRITE)."""

    def __init__(self, cwd: str, env: dict, log: Path, t0: float) -> None:
        self.password = secrets.token_urlsafe(24)
        self.env = dict(env, OPENCODE_SERVER_PASSWORD=self.password)
        self.cwd, self.t0, self.url = cwd, t0, ""
        self.p: subprocess.Popen | None = None
        self.ticks: list[float] = []  # times of LIVE events
        self.counts: dict[str, int] = {}
        self.retries: list[str] = []
        self.log = log.open("a", encoding="utf-8")
        self.listening = threading.Event()
        # localhost never goes through a proxy from the environment
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    @property
    def last(self) -> float:
        return self.ticks[-1] if self.ticks else 0.0

    def start(self, wait: float = 20) -> bool:
        """Start the server on a free port; True once it listens and its event stream is open."""
        self.p = subprocess.Popen(["opencode", "serve", "--hostname", "127.0.0.1", "--port", "0"], cwd=self.cwd,
                                  env=self.env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, start_new_session=True)
        threading.Thread(target=self._drain, daemon=True).start()
        if not self.listening.wait(wait):
            self.stop()
            return False
        threading.Thread(target=self._watch, daemon=True).start()
        return True

    def _drain(self) -> None:
        for line in self.p.stdout:
            m = re.search(r"server listening on (http://\S+)", line)
            if m and not self.url:
                self.url = m.group(1).rstrip("/")
                self.listening.set()

    def _watch(self) -> None:
        auth = "Basic " + base64.b64encode(f"opencode:{self.password}".encode()).decode()
        req = urllib.request.Request(self.url + "/api/event",
                                     headers={"Authorization": auth, "Accept": "text/event-stream"})
        while self.p and self.p.poll() is None:
            try:
                with self.opener.open(req, timeout=300) as r:
                    for raw in r:
                        line = raw.decode("utf-8", "replace").strip()
                        if line.startswith("data:"):
                            try:
                                self.seen(json.loads(line[5:]))
                            except ValueError:
                                pass
            except Exception:
                time.sleep(1)

    def seen(self, e: dict) -> None:
        now, typ = time.time(), str(e.get("type") or "")
        if LIVE.match(typ):
            self.ticks.append(now)
        self.counts[typ] = self.counts.get(typ, 0) + 1
        data = e.get("data") or {}
        row: dict = {"t": round(now - self.t0, 1), "type": typ}
        if typ.endswith(".delta"):
            row["chars"] = len(str(data.get("delta") or ""))
        else:
            row["data"] = json.dumps(data, ensure_ascii=False)[:400]
        if typ == "session.retry.scheduled":
            self.retries.append(row["data"])
        self.log.write(json.dumps(row, ensure_ascii=False) + "\n")
        self.log.flush()

    def stop(self) -> None:
        if self.p and self.p.poll() is None:
            Run.stop(self.p)
        if not self.log.closed:
            self.log.close()


def longest_gap(start: float, end: float, ticks: list[float]) -> float:
    """The longest stretch between start and end with no tick in it."""
    pts = [start] + sorted(t for t in ticks if start <= t <= end) + [end]
    return max((b - a for a, b in zip(pts, pts[1:])), default=0.0)


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


def step_times(events: Path) -> dict:
    """Split one run's wall time into model steps and tool calls, from its event stream.

    Each `step_finish` closes a model turn and the gap to the next `step_start` is the tool call that
    turn asked for. Measured 2026-11-10 on two life-overview runs (73 steps, 584 s; 38 steps, 312 s):
    about 5 s of model and 2.6 s of tool plumbing per step, whatever the tool, so the wall time
    follows the step count and nothing else.
    """
    try:
        rows = [json.loads(l) for l in events.read_text(encoding="utf-8").splitlines() if l.strip()]
    except (OSError, ValueError):
        return {}
    starts = [r for r in rows if r.get("type") == "step_start"]
    fins = [r for r in rows if r.get("type") == "step_finish"]
    if not fins:
        return {}
    tools: dict[str, list[str]] = {}
    for r in rows:
        if r.get("type") == "tool_use":
            part = r.get("part") or {}
            tools.setdefault(part.get("messageID"), []).append(part.get("tool") or "?")
    model = sum((f["timestamp"] - s["timestamp"]) / 1000 for s, f in zip(starts, fins))
    steps, per, gaps = [], {}, 0.0
    for i, (s, f) in enumerate(zip(starts, fins)):
        part = f.get("part") or {}
        what = ",".join(tools.get(part.get("messageID"), [])) or "(text)"
        steps.append({"n": i + 1, "s": (f["timestamp"] - s["timestamp"]) / 1000, "what": what,
                      "reason": part.get("reason")})
        if i + 1 < len(fins):
            g = (starts[i + 1]["timestamp"] - f["timestamp"]) / 1000
            gaps += g
            per.setdefault(what, []).append(g)
    return {"steps": steps, "model": model, "tool": gaps, "per": per,
            "span": (fins[-1]["timestamp"] - starts[0]["timestamp"]) / 1000}


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
    POLL = 5  # seconds between checks of the idle cut while `opencode run` is silent

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
        self.server: Server | None = None
        self.run_ticks: list[float] = []  # times of the lines `opencode run` printed

    def say(self, line: str) -> None:
        print(f"{time.strftime('%H:%M:%S')} {line}", flush=True)

    def env(self) -> dict:
        # opencode takes its project from $PWD, which a child inherits from the launching shell, not from
        # its working directory: launched from agentkit, it looked for the agent there and answered
        # 'Agent not found: "socrates"' (2026-11-07, hanji_test.py).
        env = dict(os.environ, NOTE_BUILD_SOCRATES=str(self.a.cwd), PWD=str(self.a.cwd))
        if getattr(self.a, "write", None):
            env["NOTE_BUILD_WRITE"] = str(Path(self.a.write).resolve())
        if self.server:
            env["OPENCODE_SERVER_PASSWORD"] = self.server.password
        return env

    def start_server(self) -> None:
        """Start the private server whose event stream is the run's sign of life (class Server)."""
        s = Server(self.a.cwd, self.env(), self.out / "server_events.jsonl", self.t0)
        if s.start():
            self.server = s
            self.say(f"SERVER {s.url}: its event stream counts as the model streaming")
        else:
            self.say("SERVER did not start in 20 s: running --standalone, where a reasoning step longer than "
                     f"--idle ({self.a.idle} s) looks dead")

    def launch(self, model: str, message: str) -> subprocess.Popen:
        where = ["--server", self.server.url] if self.server else ["--standalone"]
        cmd = ["opencode", "run", *where, "--agent", self.a.agent, "-m", model, "--format", "json",
               "--title", self.a.title]
        if self.session:
            cmd += ["--session", self.session]
        err = (self.out / "opencode.stderr").open("a")
        # stdin closed: opencode reads a piped stdin as message text and waits on it, silent (2026-11-07)
        return subprocess.Popen(cmd + [message], cwd=self.a.cwd, env=self.env(), stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=err, text=True, start_new_session=True)

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
        last = told = time.time()
        retries = len(self.server.retries) if self.server else 0
        why = ""
        try:
            while True:
                try:
                    line = q.get(timeout=self.POLL)
                except queue.Empty:
                    now = time.time()
                    alive = max(last, self.server.last if self.server else 0.0)
                    if self.server and len(self.server.retries) > retries:
                        retries = len(self.server.retries)
                        self.say(f"RETRY {self.server.retries[-1][:200]}")
                    if now - alive > self.a.idle:
                        why = f"idle {self.a.idle} s"
                    elif now - self.t0 > self.a.budget:
                        why = f"over the {self.a.budget} s budget"
                    elif now - last > 60 and now - told > 60 and alive > last:
                        # a Monitor reading these lines sees the model is streaming while `opencode run` is silent
                        told = now
                        n = sum(1 for t in self.server.ticks if t > last)
                        self.say(f"STREAMING {n} server events in {now - last:.0f} s without a line from opencode run")
                    if why:
                        break
                    continue
                if line is None:
                    why = "turn ended"
                    break
                last = time.time()
                self.run_ticks.append(last)
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                self.events.write(json.dumps({"t": round(last - self.t0, 1), "model": model, **e}, ensure_ascii=False) + "\n")
                self.session = self.session or e.get("sessionID")
                why = self.event(e, seg)
                if why:
                    break
        finally:
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

    def probe(self, model: str) -> bool:
        """A one-word ping before the run: does the provider answer within --probe seconds?

        Chaehan, 2026-11-08: "you should test the api for availability and then max 2min timeout", and
        2026-11-10: "fix the probe it costs just a few seconds as a ping". Measured 2-4 s a provider
        through the same `opencode run` path the build uses, so the default cap is 8 s."""
        t0 = time.time()
        try:
            out = subprocess.run(["opencode", "run", "--standalone", "--agent", self.a.agent, "-m", model,
                                  "--format", "json", "--title", "availability probe",
                                  "Reply with the single word OK."],
                                 cwd=self.a.cwd, capture_output=True, text=True, timeout=self.a.probe,
                                 stdin=subprocess.DEVNULL,
                                 # opencode finds the agent through $PWD, as in launch(): launched from agentkit,
                                 # the probe failed in 1 s with no answer (2026-11-09)
                                 env=dict(os.environ, PWD=str(self.a.cwd)))
            ok = '"type":"text"' in out.stdout.replace(" ", "") or '"step_finish"' in out.stdout
        except subprocess.TimeoutExpired:
            ok = False
        self.say(f"PROBE {model}: {'answers' if ok else 'no answer'} in {time.time() - t0:.0f} s")
        return ok

    def go(self) -> int:
        if self.a.write:
            message = WRITE_BRIEF.format(nb=Path(__file__).with_name("note_build.py"), d=Path(self.a.write).resolve())
        else:
            message = Path(self.a.brief).read_text(encoding="utf-8").strip()
        providers = PROVIDERS[PROVIDERS.index(self.a.start):] if self.a.start in PROVIDERS else PROVIDERS
        providers = [p.split("#")[0] + "#" + self.a.variant for p in providers]
        code, why = 6, ""
        try:
            for i, model in enumerate(providers):
                if self.a.probe and not self.probe(model):
                    why = "provider error"
                    continue
                if not self.server:
                    self.start_server()
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
        finally:
            if self.server:
                self.server.stop()
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

    def expected(self) -> bool:
        """Every file --expect names exists, is not empty and was written during this run."""
        return all(p.is_file() and p.stat().st_size and p.stat().st_mtime > self.t0
                   for p in map(Path, self.a.expect or []))

    def check_build(self) -> None:
        """Read the outcome from the build folder: opencode can move a slow write out of the event stream."""
        if self.a.expect:
            self.written = self.verified = self.expected()
            self.say(f"expected files: {'all written' if self.verified else 'missing'}")
            return
        if not self.a.build:
            return
        res = Path(self.a.build) / "write_result.txt"
        if res.exists() and res.stat().st_mtime > self.t0:
            # The bridge's own verdict: the text verify and the photo checks of this write.
            out = res.read_text(encoding="utf-8")
            self.written = '"written": true' in out
            self.verified = self.written and "PASS" in out and "VERIFY FAILED" not in out
            self.say(f"build folder: written, {out.strip().splitlines()[-1][:160]}")
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
                 f"Brief: {Path(self.a.brief).resolve() if self.a.brief else 'write ' + str(self.a.write)}; "
                 f"project folder {self.a.cwd}; agent {self.a.agent}.", "",
                 "## Providers used", "", "| Model | Start | End | Steps | Tokens | Cost USD | Ended because |",
                 "| --- | --- | --- | --- | --- | --- | --- |"]
        lines += [f"| {s['model']} | {hm(s['start'])} | {hm(s['end'] or time.time())} | {s['steps']} | {s['tokens']} | "
                  f"{s['cost']:.4f} | {s['why']} |" for s in self.segments]
        lines += ["", "## Silences", ""]
        if self.server:
            c = self.server.counts
            lines += [f"The cut falls after {self.a.idle} s in which neither `opencode run` nor its server's event stream "
                      f"shows the model working. The server sent {c.get('session.reasoning.delta', 0)} reasoning deltas, "
                      f"{c.get('session.text.delta', 0)} text deltas and {c.get('session.tool.input.delta', 0)} tool input "
                      f"deltas, and scheduled {len(self.server.retries)} provider retries.", "",
                      "| Model | Longest without a line from opencode run (s) | Longest without any sign of life (s) |",
                      "| --- | --- | --- |"]
            for s in self.segments:
                end = s["end"] or time.time()
                lines.append(f"| {s['model']} | {longest_gap(s['start'], end, self.run_ticks):.0f} | "
                             f"{longest_gap(s['start'], end, self.run_ticks + self.server.ticks):.0f} |")
        else:
            lines += [f"No server ran: the cut fell after {self.a.idle} s without a line from `opencode run --standalone`, "
                      "which prints nothing while the model reasons."]
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
        tm = step_times(self.out / "events.jsonl")
        if tm:
            n = len(tm["steps"])
            lines += ["", "## Where the time went", "",
                      f"{n} timed steps took {tm['model']:.0f} s of model time and {tm['tool']:.0f} s of tool calls: "
                      f"{tm['model'] / n:.1f} s a step against {tm['tool'] / max(n - 1, 1):.1f} s a tool call.", "",
                      "| Step's tool | Calls | Tool time (s) | Avg (s) |", "| --- | --- | --- | --- |"]
            lines += [f"| {k} | {len(v)} | {sum(v):.0f} | {sum(v) / len(v):.1f} |"
                      for k, v in sorted(tm["per"].items(), key=lambda kv: -sum(kv[1]))]
            lines += ["", "| Slowest step | s | What |", "| --- | --- | --- |"]
            lines += [f"| {x['n']} | {x['s']:.1f} | {x['what']} |"
                      for x in sorted(tm["steps"], key=lambda x: -x["s"])[:8]]
        lines += ["", "## The agent's last message", "", self.last_text.strip() or "(none)", ""]
        (self.out / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--brief", help="the message the agent gets, as a file")
    ap.add_argument("--write", help="a build folder whose draft passed the gate: the agent writes it, nothing else")
    ap.add_argument("--expect", nargs="+", help="files the run must leave; they decide the outcome of a run without a note write")
    ap.add_argument("--out", required=True, help="folder for report.md and events.jsonl")
    ap.add_argument("--session", help="continue this opencode session, e.g. with Chaehan's answers as the brief")
    ap.add_argument("--cwd", default=str(SOCRATES), help="the project folder the agent runs in")
    ap.add_argument("--build", help="the note_build folder the brief names; its read-back decides written and verified")
    ap.add_argument("--agent", default="socrates")
    ap.add_argument("--title", default="note build test")
    ap.add_argument("--start", default=PROVIDERS[0], help="first provider to try")
    ap.add_argument("--variant", default="high", choices=["low", "high", "max"],
                    help="DeepSeek's reasoning variant for every provider (opencode offers low, high and max; no setting "
                         "turns thinking off)")
    ap.add_argument("--idle", type=int, default=120, help="seconds without a streamed event before the run stops (RULES.md 73: at most 120)")
    ap.add_argument("--probe", type=int, default=8,
                    help="seconds the availability probe may take; a one-word answer costs 2-4 s, so 8 s is a ping "
                         "and a provider that misses it is down. 0 skips the probe")
    ap.add_argument("--budget", type=int, default=1500, help="seconds the whole run may take")
    a = ap.parse_args(argv)
    if not (a.brief or a.write):
        ap.error("give --brief, or --write with a build folder")
    if a.write and not a.build:
        a.build = a.write  # the folder's write_result.txt decides the outcome
    return Run(a).go()


if __name__ == "__main__":
    sys.exit(main())
