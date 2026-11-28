"""The reply gate (scripts/reply_gate.py): core 4's check, run by the harness.

The contract: the reply is the assistant's text after the turn's last tool
call; a flag blocks once and a second pass never does; a warn blocks only in
strict mode; code fences and quotes are not read; an error lets the reply go.
"""
from __future__ import annotations

import importlib.util
import io
import json
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "reply_gate.py"
_spec = importlib.util.spec_from_file_location("reply_gate", SCRIPT_PATH)
assert _spec and _spec.loader
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)

BAD = "- **No gate on chat replies.** So the shape is: two sessions."
GOOD = "The clinic opens at 9 on Monday. You still need the referral."


def _transcript(tmp_path, final_text: str) -> Path:
    rows = [
        {"type": "user", "message": {"role": "user", "content": "Is another session due?"}},
        {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "Checking."}]}},
        {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "tool_use", "id": "t1", "name": "Bash", "input": {}}]}},
        {"type": "user", "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t1", "content": "ok"}]}},
        {"type": "attachment"},
        {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": final_text}]}},
        {"type": "assistant", "isSidechain": True, "message": {"role": "assistant", "content": [{"type": "text", "text": "You a. You b. You c."}]}},
    ]
    p = tmp_path / "t.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return p


def _run_stop(monkeypatch, capsys, tmp_path, payload: dict) -> str:
    monkeypatch.setattr(gate, "LOG", tmp_path / "log.jsonl")
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
    assert gate.main(["--claude-stop"]) == 0
    return capsys.readouterr().out


def test_the_reply_is_the_text_after_the_last_tool_call(tmp_path) -> None:
    assert gate.reply_from_transcript(str(_transcript(tmp_path, GOOD))) == GOOD


def test_a_flagged_reply_is_sent_back_with_its_lines(monkeypatch, capsys, tmp_path) -> None:
    t = _transcript(tmp_path, BAD)
    out = _run_stop(monkeypatch, capsys, tmp_path, {"transcript_path": str(t), "stop_hook_active": False})
    decision = json.loads(out)
    assert decision["decision"] == "block"
    assert "bold lead-in" in decision["reason"] and "colon frame" in decision["reason"]
    assert "No gate on chat replies" in decision["reason"]
    logged = json.loads((tmp_path / "log.jsonl").read_text().splitlines()[-1])
    assert logged["blocked"] is True and logged["flags"] >= 2


def test_the_second_pass_is_never_blocked(monkeypatch, capsys, tmp_path) -> None:
    t = _transcript(tmp_path, BAD)
    assert _run_stop(monkeypatch, capsys, tmp_path, {"transcript_path": str(t), "stop_hook_active": True}) == ""


def test_a_clean_reply_passes(monkeypatch, capsys, tmp_path) -> None:
    t = _transcript(tmp_path, GOOD)
    assert _run_stop(monkeypatch, capsys, tmp_path, {"transcript_path": str(t)}) == ""


def test_the_hooks_own_last_message_wins(monkeypatch, capsys, tmp_path) -> None:
    t = _transcript(tmp_path, GOOD)
    out = _run_stop(monkeypatch, capsys, tmp_path, {"transcript_path": str(t), "last_assistant_message": BAD})
    assert json.loads(out)["decision"] == "block"


def test_an_error_lets_the_reply_go(monkeypatch, capsys, tmp_path) -> None:
    out = _run_stop(monkeypatch, capsys, tmp_path, {"transcript_path": str(tmp_path / "missing.jsonl")})
    assert out == ""
    assert "error" in json.loads((tmp_path / "log.jsonl").read_text().splitlines()[-1])


def test_a_warn_blocks_only_in_strict_mode(tmp_path) -> None:
    p = tmp_path / "r.md"
    p.write_text("Book the clinic. Bring the referral. Keep the receipt.\n")
    assert gate.main([str(p)]) == 0
    assert gate.main(["--strict", str(p)]) == 2


def test_fences_and_quotes_are_not_read(tmp_path) -> None:
    p = tmp_path / "r.md"
    p.write_text("The command is below.\n\n```\nflag — in order to leverage\n```\n\n> In order to leverage it\n")
    assert gate.main([str(p)]) == 0
