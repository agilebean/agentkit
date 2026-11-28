#!/usr/bin/env python3
"""The reply gate: core 4's wording check, run on every chat reply by the harness.

Core 4 asks the agent to lint each finished text, a chat reply included, and an
agent under a long task skips that step first (the 2026-11-28 architecture
review in socrates `agent/`, finding 1). The gate runs the same check without
being asked: the marker list of `wording_lint.py`, its run-level checks
(sentences opening with "You", paragraphs of only instructions, colon frames,
bold lead-ins, thousand separators) and the Han script check.

Usage:
  reply_gate.py --claude-stop            Claude Code Stop hook: the hook's JSON on stdin
  reply_gate.py [--strict] FILE | -      any harness: the reply's text in a file or on stdin

A reply with a flag is sent back once: Claude Code gets {"decision": "block"}
with the hits as the reason, and the agent posts the reply again, rewritten.
A warn is listed only when a flag blocks; `--strict` (or REPLY_GATE_STRICT=1)
blocks on a warn too. The second pass is never blocked again
(`stop_hook_active`), so a reply costs at most one rewrite. Code fences, quoted
lines and declared excerpts are not the writer's prose and are not read.

Every run appends one line to ~/.cache/agentkit/reply-gate/log.jsonl (words,
flags, warns, blocked), the record that shows whether the standard is active.
The gate fails open: an error is logged and the reply goes through.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys
import time
from pathlib import Path

_LINT_PATH = Path(__file__).resolve().parent / "wording_lint.py"
_spec = importlib.util.spec_from_file_location("wording_lint", _LINT_PATH)
assert _spec and _spec.loader
wording = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wording)

LOG = Path(os.environ.get("REPLY_GATE_LOG") or Path.home() / ".cache/agentkit/reply-gate/log.jsonl")
MAX_LISTED = 12


def reply_from_transcript(path: str) -> str:
    """The text of the last reply in a Claude Code transcript: the assistant's
    text after the turn's last tool call, subagent entries left out."""
    entries = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    texts: list[str] = []
    for entry in reversed(entries):
        if entry.get("isSidechain"):
            continue
        kind = entry.get("type")
        if kind == "user":
            break
        if kind != "assistant":
            continue
        content = (entry.get("message") or {}).get("content")
        if isinstance(content, str):
            texts.append(content)
            continue
        stop = False
        for block in reversed(content or []):
            if block.get("type") == "text":
                texts.append(block.get("text", ""))
            elif block.get("type") == "tool_use":
                stop = True
                break
        if stop:
            break
    return "\n\n".join(reversed([t for t in texts if t.strip()]))


def prose_only(text: str) -> str:
    """The text with code fences and quoted lines blanked, line numbers kept."""
    out, in_fence = [], False
    for line in text.splitlines():
        if wording.FENCE.match(line):
            in_fence = not in_fence
            out.append("")
        elif in_fence or line.lstrip().startswith(">"):
            out.append("")
        else:
            out.append(line)
    return "\n".join(out)


def check(text: str) -> list[tuple[int, str, str, str]]:
    """Every hit in a reply: (line, level, the words, the fix)."""
    prose = prose_only(text)
    hits = wording.lint_text(prose, wording.load_robot_markers()) + wording.rhythm_hits(text)
    for lineno, char, _line in wording.script_hits(prose):
        hits.append((lineno, "flag", char, "Han characters: write it in the thread's language (RULES.md 217)"))
    return sorted(set(hits))


def blocks(hits, strict: bool) -> bool:
    return any(level == "flag" or strict for _l, level, _m, _f in hits)


def reason(hits, text: str) -> str:
    lines = text.splitlines()
    rows = []
    for lineno, level, match, fix in hits[:MAX_LISTED]:
        where = lines[lineno - 1].strip()[:90] if 0 < lineno <= len(lines) else ""
        rows.append(f"- line {lineno}, {level} '{match}': {fix}. The line: \"{where}\"")
    more = f"\n- and {len(hits) - MAX_LISTED} more" if len(hits) > MAX_LISTED else ""
    return ("The reply gate (agentkit scripts/reply_gate.py, core 4) found these in the reply you just sent:\n"
            + "\n".join(rows) + more +
            "\nSend the reply again, whole, with each of these lines rewritten and every fact kept. "
            "Open with the answer itself and say nothing about the rewrite.")


def log(record: dict) -> None:
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass


def claude_stop(strict: bool) -> int:
    record = {"time": time.strftime("%Y-%m-%dT%H:%M:%S"), "harness": "claude-code"}
    try:
        data = json.load(sys.stdin)
        record.update(session=data.get("session_id"), cwd=data.get("cwd"))
        if data.get("stop_hook_active"):
            record["second_pass"] = True
        text = data.get("last_assistant_message")
        if not isinstance(text, str) or not text.strip():
            text = reply_from_transcript(data.get("transcript_path", ""))
        hits = check(text)
        record.update(words=len(text.split()), flags=sum(h[1] == "flag" for h in hits),
                      warns=sum(h[1] == "warn" for h in hits))
        blocked = bool(text.strip()) and blocks(hits, strict) and not data.get("stop_hook_active")
        record["blocked"] = blocked
        log(record)
        if blocked:
            print(json.dumps({"decision": "block", "reason": reason(hits, text)}))
        return 0
    except Exception as error:  # the gate must never break a session
        record["error"] = repr(error)[:300]
        log(record)
        return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--claude-stop", action="store_true", help="read a Claude Code Stop hook's JSON on stdin")
    ap.add_argument("--strict", action="store_true", help="a warn blocks as a flag does")
    ap.add_argument("file", nargs="?", help="the reply's text, or - for stdin")
    args = ap.parse_args(argv)
    strict = args.strict or os.environ.get("REPLY_GATE_STRICT") == "1"
    if args.claude_stop:
        return claude_stop(strict)
    if not args.file:
        ap.error("give FILE, - or --claude-stop")
    text = sys.stdin.read() if args.file == "-" else open(args.file, encoding="utf-8").read()
    hits = check(text)
    if blocks(hits, strict):
        print(reason(hits, text))
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
