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
