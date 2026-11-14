"""The date-analysis skill: its MacWhisper reader, its marker list and its check.

The 2026-11-10 note on the second meeting with Jiyoung Kim passed every check of
its day while Chaehan found it robotic ("took no exit, mechanisms, contrasts (and
had not), her own line is closed") and thin on her personality. These tests hold
that those sentences now fail, that plain versions pass, and that a quote is
checked against the turn its time names.
"""
from __future__ import annotations

import importlib.util
import sqlite3
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1] / "skills" / "date-analysis"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, SKILL / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


check = _load("date_check")
mw = _load("mw_transcript")

TRANSCRIPT = """# test

T0001 [0:00:00] Chaehan: 오늘 어땠어요?
T0002 [0:00:05] Jiyoung: 이해는 할 수 있어요. 이해하는데 나는 안하고 싶어.
T0003 [0:00:20] Chaehan: 그렇구나.
T0004 [0:00:25] Jiyoung: 네.
T0005 [0:00:30] Chaehan: 맛있어요.
T0006 [1:02:03] Jiyoung: 재현씨랑 있으면 약간 편하게 그냥 내가 될 수 있겠다
"""


def _turns(tmp_path):
    p = tmp_path / "t.md"
    p.write_text(TRANSCRIPT, encoding="utf-8")
    return check.load_turns(str(p))


ROBOTIC = [
    "You gave it 8.5 hours, lunch into night, and took no exit.",
    "Her own line is closed.",
    "Your turns mostly explain a mechanism.",
    "She had wanted to ask how open you are and had not.",
    "You passed the two tests she ran under the conversation.",
    "Her complaint about most people is the mirror of it.",
    "The remaining asymmetry is not volume but function.",
    "What would reverse this reading: she goes quiet.",
]
PLAIN = [
    "You stayed together 8.5 hours, from lunch until late at night, and neither of you tried to end it.",
    "She would not want an open relationship herself.",
    "You mostly explained how things work: how mezcal is made, why breathing calms you.",
    "She had wondered how open you are about relationships but did not dare to ask.",
    "She asked you two things that mattered to her, and she liked both answers.",
]


def test_the_robotic_sentences_of_the_2026_11_10_note_fail() -> None:
    for s in ROBOTIC:
        assert check.wording(s + "\n", ""), s


def test_their_plain_versions_pass() -> None:
    for s in PLAIN:
        assert check.wording(s + "\n", "") == [], s


def test_chaehans_own_words_are_left_alone() -> None:
    his = "I liked her style, although the skirt was too long."
    assert check.wording(his + "\n", "")
    assert check.wording(his + "\n", his) == []


def test_a_quote_is_found_in_the_turn_its_time_names(tmp_path) -> None:
    turns = _turns(tmp_path)
    ok = '- She said "이해는 할 수 있어요 ... 나는 안하고 싶어" [0:00:05].\n'
    fails, n = check.quotes(ok, turns)
    assert fails == [] and n == 1


def test_a_quote_without_its_time_or_at_the_wrong_time_fails(tmp_path) -> None:
    turns = _turns(tmp_path)
    assert check.quotes('- "나는 안하고 싶어".\n', turns)[0]
    assert check.quotes('- "나는 안하고 싶어" [0:00:06].\n', turns)[0]
    far = '- "재현씨랑 있으면" [0:00:05].\n'
    assert check.quotes(far, turns)[0], "a quote from an hour later is not in the turns around 0:00:05"


def test_two_quotes_on_one_line_each_need_a_time(tmp_path) -> None:
    turns = _turns(tmp_path)
    line = '- "오늘 어땠어요?" [0:00:00] and "재현씨랑 있으면" [1:02:03].\n'
    assert check.quotes(line, turns) == ([], 2)


def _draft(sex_quotes: int, filler_words: int = 0) -> str:
    q = '- "나는 안하고 싶어" [0:00:05].\n'
    out = []
    for h in check.SECTIONS:
        body = q * sex_quotes if h == "Sex and past relationships" else ""
        out.append(f"## {h}\n\nYou met her.\n\n{body}\n")
    return "".join(out) + ("word " * filler_words)


def test_sections_depth_and_length() -> None:
    assert check.sections(_draft(3)) == []
    assert any("depth" in f for f in check.sections(_draft(2)))
    assert any("length" in f for f in check.sections(_draft(3, 1600)))
    missing = _draft(3).replace("## What you can do better", "## Plans")
    assert any("What you can do better" in f for f in check.sections(missing))


def _fake_db(tmp_path) -> Path:
    db = tmp_path / "main.sqlite"
    con = sqlite3.connect(db)
    con.executescript("""
      create table session (id blob primary key, dateCreated text, originalFilename text, userChosenTitle text,
        transcriptionDidSucceed boolean, hasBeenDiarized boolean, playbackDuration double, dateDeleted double);
      create table speaker (id blob primary key, name text);
      create table transcriptline (id blob primary key, text text, start integer, "end" integer,
        sessionId blob, speakerID blob, orderIndex integer);
    """)
    con.execute("insert into session values (x'01', '2026-11-11', 'Date3', null, 1, 1, 7200, null)")
    con.execute("insert into session values (x'02', '2026-11-12', 'Busy', null, 0, 0, 7200, null)")
    con.execute("insert into speaker values (x'a1', 'Speaker 1')")
    con.execute("insert into speaker values (x'a2', 'Speaker 2')")
    rows = [(1, "안녕하세요", 0, 2000, x) for x in [b"\xa1"]] + [
        (2, "반가워요?", 2000, 4000, b"\xa1"), (3, "네 저도요", 4000, 9000, b"\xa2"),
        (4, "다음에 또 봐요", 3_700_000, 3_705_000, b"\xa2")]
    for i, (o, t, s, e, sp) in enumerate(rows):
        con.execute("insert into transcriptline values (?, ?, ?, ?, x'01', ?, ?)", (bytes([i + 1]), t, s, e, sp, o))
    con.commit()
    con.close()
    return db


def test_mw_export_joins_a_speakers_lines_and_applies_the_map(tmp_path, capsys) -> None:
    db = _fake_db(tmp_path)
    out = tmp_path / "t.md"
    rc = mw.main(["--db", str(db), "export", "Date3", "--out", str(out),
                  "--map", "Speaker 1=Chaehan", "--map", "Speaker 2=Jiyoung"])
    assert rc == 0
    lines = [l for l in out.read_text(encoding="utf-8").splitlines() if l.startswith("T")]
    assert lines == ["T0001 [0:00:00] Chaehan: 안녕하세요 반가워요?",
                     "T0002 [0:00:04] Jiyoung: 네 저도요 다음에 또 봐요"]
    assert check.load_turns(str(out))[1][1] == "Jiyoung"


def test_mw_stats_counts_talk_time_and_questions(tmp_path) -> None:
    db = _fake_db(tmp_path)
    con = mw.open_copy(str(db))
    s = mw.find_session(con, "Date3")
    turns = mw.turns_of(mw.lines_of(con, s["id"]), {"Speaker 1": "Chaehan", "Speaker 2": "Jiyoung"})
    md = mw.stats_md(turns, "Date3")
    assert "| Jiyoung | 0 | 71% | 1 | " in md
    assert "| Chaehan | 0 | 29% | 1 | 11 | 1 |" in md, md.splitlines()[5:8]


def test_mw_refuses_a_session_still_transcribing(tmp_path, capsys) -> None:
    db = _fake_db(tmp_path)
    assert mw.main(["--db", str(db), "stats", "Busy"]) == 3


def test_a_sentence_opening_used_four_times_fails() -> None:
    four = "".join(f"You would think again if she {w}.\n" for w in ["stops", "goes", "says", "asks"])
    assert check.formula(four)
    assert check.formula(four.replace("You would think again if she asks.\n", "")) == []
    quotes = "".join(f'- "나는 안하고 싶어" [0:00:0{i}].\n' for i in range(5))
    assert check.formula(quotes) == []


def test_the_think_again_formula_is_a_marker() -> None:
    assert check.wording("You would think again if she goes quiet.\n", "")
