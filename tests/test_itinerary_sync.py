"""itinerary-sync: the row rules Chaehan set on 2026-11-07, on a synthetic note and records."""
import importlib.util
import json
import sys
from pathlib import Path

_p = Path(__file__).resolve().parents[1] / "skills" / "itinerary-sync" / "scripts" / "itinerary_sync.py"
_s = importlib.util.spec_from_file_location("itinerary_sync", _p)
its = importlib.util.module_from_spec(_s)
sys.modules["itinerary_sync"] = its
_s.loader.exec_module(its)

G26, G27 = "11111111-1111-1111-1111-111111111111", "22222222-2222-2222-2222-222222222222"
BOOK = "33333333-3333-3333-3333-333333333333"


def row(date, city, det="/", eur="/"):
    return f"<tr><td>{date}</td><td>{city}</td><td>/</td><td>{det}</td><td>/</td><td>{eur}</td><td>/</td></tr>"


HEAD = "<tr><th>Date</th><th>City</th><th>Temp</th><th>Details</th><th>Orig</th><th>€</th><th>$</th></tr>"


def note(h2, rows):
    return f'<en-note><h2>{h2}</h2><table>{HEAD}{"".join(rows)}</table></en-note>'


def repo(tmp_path):
    m = tmp_path / "memory"
    m.mkdir()
    (m / "travelitinerary.csv").write_text("date,city\n2026-12-12,Melbourne\n2027-03-01,Osaka\n2027-03-25,Seoul\n")
    (m / "travel.md").write_text(
        f"## Itinerary\n- notes: 2026 Travel Itinerary `{G26}`, 2027 Travel Itinerary `{G27}`\n\n"
        "## 2027 schedule\n\n| Date | Move | Purpose / note |\n|---|---|---|\n"
        "| 2026-12-12 | Osaka → Melbourne | block |\n| 2027-03-01 | Melbourne → Osaka | spring |\n"
        "| 2027-03-25 | Osaka → Seoul | course |\n\n## Next\n")
    return tmp_path


NOTES = {
    G26: note("2409€/m [12m] -> €100+200 = 300 | $/€=1.17", [row("2026-12-12 SAT ✅", "Melbourne", "UKO unit")]),
    G27: note("19313+343=22709", [row("2026-12-12", "Melbourne 11w"), row("2027-03-01", "Osaka 4w"),
                                  row("2027-03-25", "Seoul 12w")]),
}
FLIGHT = {"kind": "flight", "from": "Melbourne", "to": "Osaka", "depart": "2027-03-01", "arrive": "2027-03-02",
          "price": 2092, "currency": "EUR", "split": 2, "note_guid": BOOK, "note_title": "Flug MEL-KIX"}


def plan(tmp_path, events, notes=NOTES):
    p = its.Plan(events, repo(tmp_path), dict(notes))
    p.run()
    return p


def applied(p, n):
    enml = n.enml
    for op in p.ops(n):
        assert enml.count(op["find"]) == 1
        enml = enml.replace(op["find"], op["content"])
    return enml


def test_an_overnight_flight_moves_the_unbooked_row_to_the_landing_day(tmp_path):
    p = plan(tmp_path, [FLIGHT])
    n27 = p.notes[2027]
    after = applied(p, n27)
    assert "2027-03-02 TUE" in after and "Flight ✅" in after and BOOK in after
    assert "Osaka 3w" in after and ">1046<" in after and ">1224<" in after
    assert "87€/m [12m]" in after and "€1046 = 1046" in after
    assert [str(r.date) for r in p.csv_rows if r.city == "Osaka"] == ["2027-03-02"]


def test_a_date_never_moves_a_booked_row(tmp_path):
    booked = dict(NOTES)
    booked[G27] = NOTES[G27].replace("<td>2027-03-25</td>", "<td>2027-03-25 THU ✅</td>")
    p = plan(tmp_path, [{"kind": "dates", "city": "Seoul", "date": "2027-03-16"}], booked)
    assert p.asks and not p.ops(p.notes[2027])
    assert [str(r.date) for r in p.csv_rows if r.city == "Seoul"] == ["2027-03-25"]


def test_a_stay_across_the_new_year_splits_its_euro_by_nights(tmp_path):
    uko = {"kind": "apartment", "city": "Melbourne", "checkin": "2026-12-12", "checkout": "2027-03-01",
           "price": 1185, "currency": "AUD", "eur": 790, "provider": "UKO Melbourne Central",
           "note_guid": BOOK, "note_title": "UKO lease"}
    p = plan(tmp_path, [uko])
    a26, a27 = applied(p, p.notes[2026]), applied(p, p.notes[2027])
    assert BOOK in a26 and BOOK in a27
    assert ">200<" not in a26  # the 2026 row already names UKO: its 20 nights were costed by hand
    assert ">590<" in a27 and "UKO Melbourne Central 2027: 59 nights × €10 = 590" in a27 and "AUD 885" in a27
    assert "€590 = 590" in a27
    p2 = its.Plan([uko], tmp_path, {G26: a26, G27: a27})
    p2.run()
    assert not p2.ops(p2.notes[2026]) and not p2.ops(p2.notes[2027])


def test_a_new_city_inserts_a_row_and_a_second_run_changes_nothing(tmp_path):
    kyoto = {"kind": "hotel", "city": "Kyoto", "checkin": "2027-03-04", "checkout": "2027-03-05",
             "note_guid": BOOK, "note_title": "Kyoto hotel"}
    p = plan(tmp_path, [kyoto])
    after = applied(p, p.notes[2027])
    assert after.index("Kyoto 1d") > after.index("Osaka") and "Hotel ✅" in after
    assert any("2027-03-05" in a for a in p.asks)
    p2 = its.Plan([kyoto], tmp_path, {G26: NOTES[G26], G27: after})
    p2.run()
    assert not p2.ops(p2.notes[2027])


def test_a_missing_landing_day_is_refused():
    bad = dict(FLIGHT, arrive=None)
    assert any("arrive" in e for e in its.validate({"events": [bad]}))


def test_the_enml_is_found_inside_an_mcp_result():
    wrapped = {"content": [{"type": "text", "text": json.dumps({"content": NOTES[G27]})}]}
    assert its.find_enml(wrapped) == NOTES[G27]
