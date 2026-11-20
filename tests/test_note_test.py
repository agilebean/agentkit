import importlib.util
from pathlib import Path

_p = Path(__file__).resolve().parents[1] / "skills" / "evernote" / "scripts" / "note_test.py"
_spec = importlib.util.spec_from_file_location("note_test", _p)
nt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(nt)


def test_next_output_is_classified() -> None:
    assert nt.classify_next("Assembled x\n\nPASS. The note text is stamped. Write it")[0] == "pass"
    assert nt.classify_next("Ask Chaehan with the question tool\n- Maps and links\n") == ("ask", ["- Maps and links"])
    kind, lines = nt.classify_next("Fix new.tsv:\n- D2 summary line uses a contrast\n- D3 heading has 9 words\n")
    assert kind == "fix" and len(lines) == 2
    assert nt.classify_next("Step 2 of 3: labels.\n\n- not a failure\n") == ("step", [])


def test_two_rounds_without_progress_on_the_same_failure_are_stuck() -> None:
    r = nt.Rounds()
    for n in (2, 2):
        r.add(0, "fix", [f"- T12 8 list items at one level in 'Getting around'"] * n)
    assert r.stuck() is None
    r.add(0, "fix", ["- T12 9 list items at one level in 'Getting around'"] * 2)
    assert r.stuck()


def test_a_falling_count_or_a_new_failure_is_progress() -> None:
    r = nt.Rounds()
    r.add(0, "fix", ["- a", "- b", "- c"])
    r.add(0, "fix", ["- a", "- b"])
    r.add(0, "fix", ["- a", "- b"])
    assert r.stuck() is None
    r2 = nt.Rounds()
    for first in ("- new.tsv D1", "- titles.tsv 5", "- edits.tsv 3"):
        r2.add(0, "fix", [first])
    assert r2.stuck() is None
    r2.add(0, "step", [])
    assert r2.fixes == []


def test_a_spent_quota_is_a_provider_error() -> None:
    assert nt.PROVIDER_ERROR.search('{"type": "provider.quota", "message": "Go usage limit exceeded", "status": 429}')
    assert nt.PROVIDER_ERROR.search("Upstream request failed: Model is unavailable.")
    assert not nt.PROVIDER_ERROR.search("note_build.py: no heading contains 'Swim'")


def test_the_launch_puts_the_project_folder_in_pwd(tmp_path, monkeypatch) -> None:
    seen = {}

    class FakePopen:
        def __init__(self, cmd, cwd=None, env=None, **kw):
            seen.update(cwd=cwd, pwd=env.get("PWD"))

    monkeypatch.setattr(nt.subprocess, "Popen", FakePopen)
    monkeypatch.setenv("PWD", "/somewhere/else")
    a = type("A", (), {"out": str(tmp_path), "session": None, "agent": "socrates", "title": "t",
                       "cwd": "/Users/x/socrates"})()
    nt.Run(a).launch("m", "hello")
    assert seen == {"cwd": "/Users/x/socrates", "pwd": "/Users/x/socrates"}


def _args(tmp_path, idle):
    return type("A", (), {"out": str(tmp_path), "session": None, "agent": "socrates", "title": "t",
                          "cwd": str(tmp_path), "idle": idle, "budget": 60})()


class _SilentRun:
    """`opencode run` that prints nothing for `quiet` seconds, then one step and the end of its turn."""

    def __init__(self, quiet):
        self.quiet, self.pid = quiet, 0

    @property
    def stdout(self):
        import time
        time.sleep(self.quiet)
        yield '{"type":"step_finish","part":{"cost":0,"tokens":{}}}\n'

    def poll(self):
        return 0


def _segment(tmp_path, monkeypatch, quiet, idle, deltas):
    import threading
    import time
    run = nt.Run(_args(tmp_path, idle))
    run.POLL = 0.1
    run.server = nt.Server(str(tmp_path), {}, tmp_path / "server_events.jsonl", run.t0)
    monkeypatch.setattr(run, "launch", lambda model, message: _SilentRun(quiet))

    def stream():
        end = time.time() + quiet
        while time.time() < end:
            run.server.seen({"type": "session.reasoning.delta", "data": {"delta": "thinking"}})
            time.sleep(0.2)

    if deltas:
        threading.Thread(target=stream, daemon=True).start()
    return run.segment("m", "hello")


def test_reasoning_on_the_server_stream_keeps_a_silent_run_alive(tmp_path, monkeypatch) -> None:
    # 2026-11-17 and 2026-11-19: DeepSeek reasoned past the cut while `opencode run` printed nothing
    assert _segment(tmp_path, monkeypatch, quiet=1.5, idle=1, deltas=True) == "turn ended"


def test_true_silence_is_still_cut(tmp_path, monkeypatch) -> None:
    assert _segment(tmp_path, monkeypatch, quiet=1.5, idle=1, deltas=False) == "idle 1 s"


def test_a_provider_retry_is_not_a_sign_of_life(tmp_path) -> None:
    s = nt.Server(str(tmp_path), {}, tmp_path / "e.jsonl", 0)
    s.seen({"type": "session.retry.scheduled", "data": {"attempt": 1}})
    s.seen({"type": "server.connected", "data": {}})
    assert s.ticks == [] and len(s.retries) == 1
    s.seen({"type": "session.tool.input.delta", "data": {"delta": "abc"}})
    assert len(s.ticks) == 1


def test_the_launch_runs_against_the_private_server_with_its_password(tmp_path, monkeypatch) -> None:
    seen = {}

    class FakePopen:
        def __init__(self, cmd, cwd=None, env=None, **kw):
            seen.update(cmd=cmd, password=env.get("OPENCODE_SERVER_PASSWORD"))

    monkeypatch.setattr(nt.subprocess, "Popen", FakePopen)
    # An opencode session sets this for its own shell tools; a launch without a private server adds none of its own.
    monkeypatch.delenv("OPENCODE_SERVER_PASSWORD", raising=False)
    run = nt.Run(_args(tmp_path, 120))
    run.launch("m", "hello")
    assert "--standalone" in seen["cmd"] and seen["password"] is None
    run.server = nt.Server(str(tmp_path), {}, tmp_path / "e.jsonl", 0)
    run.server.url = "http://127.0.0.1:1"
    run.launch("m", "hello")
    i = seen["cmd"].index("--server")
    assert seen["cmd"][i + 1] == "http://127.0.0.1:1" and seen["password"] == run.server.password


def test_longest_gap_counts_from_the_segment_start_to_its_end() -> None:
    assert nt.longest_gap(0, 10, [2, 3]) == 7
    assert nt.longest_gap(0, 10, []) == 10
    assert nt.longest_gap(0, 10, [12]) == 10
