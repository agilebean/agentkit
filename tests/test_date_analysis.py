"""The date-analysis skill: its MacWhisper reader, its marker list and its check.

The 2026-11-10 note on the second meeting with Mina Lee passed every check of
its day while Chaehan found it robotic ("took no exit, mechanisms, contrasts (and
had not), her own line is closed") and thin on her personality. These tests hold
that those sentences now fail, that plain versions pass, and that a quote is
checked against the turn its time names.
"""
from __future__ import annotations

import importlib.util
import sqlite3
from pathlib import Path

import pytest

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
T0002 [0:00:05] Mina: 이해는 할 수 있어요. 이해하는데 나는 안하고 싶어.
T0003 [0:00:20] Chaehan: 그렇구나.
T0004 [0:00:25] Mina: 네.
T0005 [0:00:30] Chaehan: 맛있어요.
T0006 [1:02:03] Mina: 재현씨랑 있으면 약간 편하게 그냥 내가 될 수 있겠다
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


def test_the_turning_point_comes_second_and_is_told_as_a_story() -> None:
    """Chaehan, 2026-11-14: the turn that changed her was missed, and sex sat too high (failure 210)."""
    assert check.SECTIONS.index("The turning point") == 1
    assert check.SECTIONS.index("Sex and past relationships") > check.SECTIONS.index("Her feelings for you")
    story = _draft(3).replace("## The turning point\n\nYou met her.",
                              "## The turning point\n\nYou asked about her hand. She told you about her fear.")
    assert check.sections(story) == []
    listed = _draft(3).replace("## The turning point\n\nYou met her.",
                               "## The turning point\n\n- You asked about her hand.\n- She told you her fear.")
    assert any("turning point" in f for f in check.sections(listed))
    # Chaehan, 2026-11-16: the section "recites the conversation like a normal summary" - 31 quotes, no idea.
    recital = _draft(3).replace("## The turning point\n\nYou met her.", "## The turning point\n\n" +
                                " ".join(f'She said "말{i}" [0:0{i % 10}:00].' for i in range(check.MAX_TURN_QUOTES + 1)))
    assert any("quotes; keep at most" in f for f in check.sections(recital))
    assert not any("quotes; keep at most" in f for f in check.sections(story))
    sex_first = _draft(3).replace("## The turning point", "## Sex and past relationships x", 1)
    assert any("order" in f or "missing" in f for f in check.sections(sex_first))


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
                  "--map", "Speaker 1=Chaehan", "--map", "Speaker 2=Mina"])
    assert rc == 0
    lines = [l for l in out.read_text(encoding="utf-8").splitlines() if l.startswith("T")]
    assert lines == ["T0001 [0:00:00] Chaehan: 안녕하세요 반가워요?",
                     "T0002 [0:00:04] Mina: 네 저도요 다음에 또 봐요"]
    assert check.load_turns(str(out))[1][1] == "Mina"


def test_mw_stats_counts_talk_time_and_questions(tmp_path) -> None:
    db = _fake_db(tmp_path)
    con = mw.open_copy(str(db))
    s = mw.find_session(con, "Date3")
    turns = mw.turns_of(mw.lines_of(con, s["id"]), {"Speaker 1": "Chaehan", "Speaker 2": "Mina"})
    md = mw.stats_md(turns, "Date3")
    assert "| Mina | 0 | 71% | 1 | " in md
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


def _md_turns():
    return _load("md_turns")


def test_md_turns_reads_chaehans_export_with_its_times(tmp_path) -> None:
    """Chaehan, 2026-11-14: the transcript is the file he exported, never MacWhisper's database again."""
    mt = _md_turns()
    export = ("**Chaehan**\n*00:03*\n무슨 무슨?\n\n*00:05*\n그러니까 겁나 사람 만날 때\n\n"
              "**Mina**\n*05:17:42*\n머리가 깨끗해지고 있는 중인 것 같아요\n")
    ts = mt.turns(export, {"Speaker 4": "Other"})
    assert [(mt.clock(s), w) for s, w, _ in ts] == [("0:00:03", "Chaehan"), ("0:00:05", "Chaehan"),
                                                     ("5:17:42", "Mina")]
    out = tmp_path / "t.md"
    src = tmp_path / "x.md"
    src.write_text(export, encoding="utf-8")
    assert mt.main([str(src), "--out", str(out)]) == 0
    turns = check.load_turns(str(out))
    assert turns[2] == ("5:17:42", "Mina", "머리가 깨끗해지고 있는 중인 것 같아요")
    assert check.quotes('"머리가 깨끗해지고" [5:17:42]', turns) == ([], 1)


def test_md_turns_refuses_an_export_without_times(tmp_path) -> None:
    mt = _md_turns()
    src = tmp_path / "x.md"
    src.write_text("**Chaehan**\n안녕하세요\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        mt.main([str(src), "--out", str(tmp_path / "t.md")])


def _lines(*rows):
    return [{"text": t, "start": s, "end": e, "speaker": w} for w, s, e, t in rows]


def test_mw_finds_a_korean_title_stored_decomposed(tmp_path) -> None:
    """The app stores 지원 decomposed (NFD); on 2026-11-20 a plain SQL match missed it."""
    import unicodedata
    db = _fake_db(tmp_path)
    con = sqlite3.connect(db)
    con.execute("insert into session values (x'03', '2026-11-19', ?, null, 1, 1, 5100, null)",
                (unicodedata.normalize("NFD", "2026-11-19 Noble Date 지원"),))
    con.commit()
    con.close()
    s = mw.find_session(mw.open_copy(str(db)), "2026-11-19 Noble Date 지원")
    assert s["id"] == b"\x03"


def test_two_unnamed_speakers_are_named_by_pitch_the_lower_voice_is_chaehan() -> None:
    lines = _lines(("Speaker 1", 0, 5000, "a"), ("Speaker 2", 5000, 9000, "b"), ("Speaker 3", 9000, 9500, "c"))
    hz = {"Speaker 1": 222.0, "Speaker 2": 171.0}
    names, how = mw.name_speakers(lines, "Joohee", "x.m4a", pitch=lambda _p, spans: hz[
        next(ln["speaker"] for ln in lines if (ln["start"], ln["end"]) == spans[0])])
    assert names == {"Speaker 2": "Chaehan", "Speaker 1": "Joohee"}, how
    assert "Speaker 3" not in names


def test_voices_too_close_or_no_audio_leave_the_speakers_unnamed() -> None:
    lines = _lines(("Speaker 1", 0, 5000, "a"), ("Speaker 2", 5000, 9000, "b"))
    assert mw.name_speakers(lines, "Joohee", "x.m4a", pitch=lambda *_: 200.0)[0] == {}
    assert mw.name_speakers(lines, "Joohee", None)[0] == {}


def test_a_name_the_app_holds_is_kept_and_the_other_speaker_takes_the_other_name() -> None:
    lines = _lines(("Chaehan", 0, 5000, "a"), ("Speaker 2", 5000, 9000, "b"))
    assert mw.name_speakers(lines, "Joohee", None)[0] == {"Speaker 2": "Joohee"}
    lines = _lines(("Chaehan", 0, 5000, "a"), ("Joohee", 5000, 9000, "b"))
    assert mw.name_speakers(lines, "X", None)[0] == {}


def test_her_name_is_what_the_title_leaves_after_date_Noble_and_date_n() -> None:
    assert mw.her_name("2026-11-19 Noble Date 지원") == "지원"
    assert mw.her_name("2026-11-15 Mina Date6") == "Mina"


def test_the_md_export_reads_like_chaehans_own_and_is_never_written_over(tmp_path) -> None:
    db = _fake_db(tmp_path)
    out = tmp_path / "Date3.md"
    assert mw.main(["--db", str(db), "md", "Date3", "--her", "Mina", "--out", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert text.startswith("# Date3\n\n**Speaker 1**\n\n*0:00:00*\n\n안녕하세요\n")
    mt = _md_turns()
    ts = mt.turns(text, {})
    assert [(mt.clock(s), w) for s, w, _ in ts][:3] == [("0:00:00", "Speaker 1"), ("0:00:02", "Speaker 1"),
                                                         ("0:00:04", "Speaker 2")]
    assert mw.main(["--db", str(db), "md", "Date3", "--out", str(out)]) == 4
