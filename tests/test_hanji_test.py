import importlib.util
import types
from pathlib import Path

_p = Path(__file__).resolve().parents[1] / "skills" / "hanji" / "scripts" / "hanji_test.py"
_spec = importlib.util.spec_from_file_location("hanji_test", _p)
ht = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ht)


def tool(command, out, exit_code, tool_name="shell", status="completed", start=1000, end=1250):
    return {"type": "tool_use", "part": {"type": "tool", "tool": tool_name, "state": {
        "status": status, "input": {"command": command} if tool_name == "shell" else {"code": command},
        "output": out, "time": {"start": start, "end": end},
        "metadata": {"metadata": {"exit": exit_code}}}}}


def run(tmp_path):
    a = types.SimpleNamespace(out=str(tmp_path), session=None, cwd="", agent="socrates", title="", start="",
                              idle=300, budget=1200, build=None, brief="")
    r = ht.HanjiRun(a)
    r.say = lambda *x: None
    return r, {"steps": 0, "cost": 0.0, "tokens": 0}


def test_calls_carry_duration_exit_and_the_helper_commands(tmp_path) -> None:
    r, seg = run(tmp_path)
    r.event(tool('P="python3 x/hanji_note.py"; $P add-row "T" "a,b" && $P update-cell "T" 1 2 v',
                 '{"verified": true}\n{"verified": true}', 0), seg)
    c = r.calls[0]
    assert (c["what"], c["ms"], c["exit"], c["verified"], c["failed"]) == ("add-row + update-cell", 250, 0, 2, False)


def test_not_found_is_an_answer_and_another_exit_is_a_failure(tmp_path) -> None:
    r, seg = run(tmp_path)
    r.event(tool('$P find "T"', '{"error": "no note titled"}', 3), seg)
    r.event(tool('$P write "T" --file f', '{"error": "the edit would remove"}', 2), seg)
    assert [c["failed"] for c in r.calls] == [False, True]
    r.check_build()
    assert r.verified is False


def test_an_mcp_execute_call_is_recorded(tmp_path) -> None:
    r, seg = run(tmp_path)
    r.event(tool("const t0 = Date.now(); await evernote.get_note({guid})", '{"read": 412}', None,
                 tool_name="execute"), seg)
    assert r.calls[0]["tool"] == "execute" and r.calls[0]["ms"] == 250 and r.calls[0]["failed"] is False


def test_an_evernote_copy_report_counts_as_verified_writes(tmp_path) -> None:
    r, seg = run(tmp_path)
    r.event(tool("python3 x/en_to_hanji.py start \"2026 New Year's Resolutions\"", "Receiver on port 1", 0), seg)
    rep = ("Moved 2 of 3 notes.\n## A\nMoved: Hanji notebook Inbox, id 1, write verified True.\n"
           "## B\nMoved: Hanji notebook Inbox, id 2, write verified True.\n## C\nNot moved: no Evernote note has this exact title.")
    r.event(tool("const B = 1; await tools.evernote.get_note({})", rep, None, tool_name="execute"), seg)
    assert r.calls[0]["what"] == "start" and r.calls[1]["verified"] == 2
    r.check_build()
    assert r.written and r.verified
    r.event(tool("const B = 1", "## D\nNot moved: hanji_note.py create exited 4: the copy did not read back", None,
                 tool_name="execute"), seg)
    r.check_build()
    assert r.verified is False


def test_the_runner_accepts_every_option_note_test_reads(monkeypatch, tmp_path) -> None:
    """note_test.Run reads its options from self.a; an option missing from hanji_test's parser crashed the
    2026-11-10 run before launch (AttributeError on probe)."""
    import re
    seen = {}
    monkeypatch.setattr(ht.HanjiRun, "go", lambda self: seen.update(a=self.a) or 0)
    assert ht.main(["--brief", "b.md", "--out", str(tmp_path)]) == 0
    names = set(re.findall(r"self\.a\.([a-z_]+)", Path(ht.note_test.__file__).read_text(encoding="utf-8")))
    assert names and not [n for n in sorted(names) if not hasattr(seen["a"], n)]
