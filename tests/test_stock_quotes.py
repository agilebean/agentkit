"""The stock-analysis skill's data script (skills/stock-analysis/scripts/quotes.py).

Covers the parts that decide a score: the listing a ticker resolves to, the price returns, the five
factors of 0-2 points (Cash, Tech, CEO, Debt, Outlook), the rank with its P/E tie-break, the hand-set
values, and the parse of Yahoo's quoteSummary and fundamentals timeseries. No test touches the network.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_p = Path(__file__).resolve().parents[1] / "skills/stock-analysis/scripts/quotes.py"
_spec = importlib.util.spec_from_file_location("stock_quotes", _p)
q = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(q)


# --- listings -------------------------------------------------------------------------------------

@pytest.mark.parametrize("given,expected", [
    ("nvd", ("NVDA", "NVD.DE")),
    ("NVD.DE", ("NVDA", "NVD.DE")),
    ("fb2a", ("META", "FB2A.DE")),
    ("arm", ("ARM", None)),
    ("6954.T", ("6954.T", None)),
])
def test_resolve_maps_a_german_listing_to_its_us_primary(given, expected):
    assert q.resolve(given) == expected


# --- returns --------------------------------------------------------------------------------------

def test_returns_over_one_and_three_months_and_the_200_day_average():
    closes = [float(i) for i in range(1, 251)]  # 1 .. 250
    r = q.returns(closes)
    assert r["price"] == 250.0
    assert r["r1m"] == pytest.approx(250 / 229 - 1)
    assert r["r3m"] == pytest.approx(250 / 187 - 1)
    assert r["ma200"] == pytest.approx(sum(range(51, 251)) / 200)


def test_returns_skip_missing_closes_and_leave_the_200_day_average_out_for_a_young_listing():
    closes = [None] + [100.0] * 110 + [None, 120.0]
    r = q.returns(closes)
    assert r["price"] == 120.0
    assert r["ma200"] is None
    assert r["r3m"] == pytest.approx(0.2)


# --- the five factors, each 0-2 points -----------------------------------------------------------

def test_windows_are_the_last_three_fiscal_years():
    assert q.windows(["2022-12-31", "2023-12-31", "2024-12-31", "2025-12-31"], "2026-03-31") == [
        "2023-12-31", "2024-12-31", "2025-12-31"]


def test_windows_take_the_latest_12_months_half_a_year_after_the_fiscal_year():
    assert q.windows(["2023-12-31", "2024-12-31", "2025-12-31"], "2026-09-30") == [
        "2024-12-31", "2025-12-31", "ttm"]
    assert q.windows(["2024-08-31", "2025-08-31", "2026-08-31"], "2026-08-31") == [
        "2024-08-31", "2025-08-31", "2026-08-31"]


def test_shares_divide_by_revenue_and_count_no_reported_rnd_as_zero():
    rev = {"a": 100.0, "b": 200.0, "ttm": 400.0}
    assert q.shares(rev, {"a": 25.0, "b": 40.0, "ttm": 100.0}, ["a", "b", "ttm"]) == [0.25, 0.2, 0.25]
    assert q.shares(rev, {}, ["a", "b"], missing_zero=True) == [0.0, 0.0]
    assert q.shares(rev, {}, ["a", "b"]) is None
    assert q.shares(rev, {"a": 1.0}, ["a", "c"]) is None    # no revenue for a window


@pytest.mark.parametrize("ratios,expected", [
    ([0.58, 0.66, 0.67], 2),    # Nvidia's EBITDA share
    ([0.198, 0.211, 0.25], 1),  # AMD: 2024 just under 20%, the average above
    ([0.17, 0.21, 0.18], 0),    # Alibaba
    ([0.20, 0.25, 0.46], 1),    # exactly 20% does not pass in that year
    (None, None),
])
def test_three_year_score(ratios, expected):
    assert q.score_three_years(ratios) == expected


@pytest.mark.parametrize("debt,cash,ebitda,expected", [
    (38.1, 97.7, 243.3, -59.6 / 243.3),   # Nvidia: net cash
    (59.4, 24.0, 52.3, 35.4 / 52.3),      # Broadcom: 0.68 years
    (169.1, 37.1, 34.4, 132.0 / 34.4),    # Oracle: 3.84 years
    (10.2, 3.5, -0.1, float("inf")),      # IREN: net debt, no EBITDA
    (None, None, 5.0, None),
])
def test_net_debt_in_years_of_ebitda(debt, cash, ebitda, expected):
    got = q.net_debt_years(debt, cash, ebitda)
    assert got == expected if expected in (None, float("inf")) else got == pytest.approx(expected)


@pytest.mark.parametrize("years,fcf,expected", [
    (-0.2, 5.0, 2),         # net cash, cash coming in
    (0.68, 5.0, 2),         # under a year of EBITDA
    (-4.3, -14.0, 1),       # net cash but burning it (SpaceX)
    (2.0, 5.0, 1),          # one to three years
    (2.0, -5.0, 0),         # both
    (3.84, 30.0, 0),        # Oracle: above three years
    (float("inf"), None, 0),
    (None, 5.0, None),
    (0.5, None, 2),         # no free cash flow figure: debt alone
])
def test_debt_score(years, fcf, expected):
    assert q.score_debt(years, fcf) == expected


@pytest.mark.parametrize("eps_now,eps_90d,expected", [
    (16.6, 12.99, 2),       # Nvidia +28%
    (1.0, 0.96, 1),         # within 5%
    (1.79, 2.03, 0),        # Intel -12%
    (-1.0, -2.0, 0),        # a loss expected
    (0.5, -0.2, 2),         # turned to a profit
    (None, 1.0, None),
])
def test_outlook_score(eps_now, eps_90d, expected):
    assert q.score_outlook(eps_now, eps_90d) == expected


def test_returns_give_the_price_3_months_ago_and_the_fall_from_the_1_year_high():
    closes = [100.0] * 100 + [200.0] + [80.0] * 100
    r = q.returns(closes)
    assert r["p3m"] == 80.0
    assert r["high"] == 200.0
    assert r["from_high"] == pytest.approx(-0.6)


def test_pe_change_divides_the_price_move_by_the_move_in_the_earnings_estimate():
    assert q.pe_change(50, 100, 2.0, 2.0) == pytest.approx(-0.5)   # price halved, estimate held: P/E halved
    assert q.pe_change(50, 100, 1.0, 2.0) == pytest.approx(0.0)    # both halved: no cheaper than before
    assert q.pe_change(68, 100, 1.28, 1.0) == pytest.approx(0.68 / 1.28 - 1)


@pytest.mark.parametrize("args", [(50, None, 2, 2), (50, 100, -1, 2), (50, 100, 2, 0), (None, 100, 2, 2)])
def test_pe_change_is_none_without_data_or_on_a_loss(args):
    assert q.pe_change(*args) is None


@pytest.mark.parametrize("when,expected", [
    ("2026-12-09", "2026-12-09"),
    ("2026-11-20", "2026-11-20"),
    ("2026-11-17", "reported 2026-11-17"),
    (None, "n/a"),
])
def test_earnings_label_marks_a_date_already_past(when, expected):
    from datetime import date
    assert q.earnings_label(when, today=date(2026, 11, 20)) == expected


# --- total, rank and hand-set values ----------------------------------------------------------

def _row(t, fpe=20.0, **pts):
    base = {"cash": 2, "tech": 1, "ceo": None, "debt": 2, "outlook": 1}
    return {"ticker": t, "held": None, "fpe": fpe, "scores": base | pts, "set": {}}


def test_total_is_the_sum_of_five_and_none_until_the_ceo_is_set():
    assert q.total({"cash": 2, "tech": 2, "ceo": 2, "debt": 2, "outlook": 2}) == 10
    assert q.total({"cash": 2, "tech": 0, "ceo": 1, "debt": 2, "outlook": 2}) == 7
    assert q.total({"cash": 2, "tech": 0, "ceo": None, "debt": 2, "outlook": 2}) is None


def test_rank_puts_the_higher_score_first_and_breaks_ties_by_the_lower_pe():
    rows = [_row("A", fpe=28.0) | {"total": 7}, _row("B", fpe=9.0) | {"total": 7},
            _row("C", fpe=3.0) | {"total": 5}, _row("D", fpe=-25.0) | {"total": 7},
            _row("E") | {"total": None}]
    assert [r["ticker"] for r in sorted(rows, key=q.rank_key)] == ["B", "A", "D", "C", "E"]


def test_override_sets_the_ceo_by_either_listing_and_recomputes_the_total():
    rows = [_row("NVDA"), _row("ORCL")]
    rows[0]["held"] = "NVD.DE"
    q.apply_overrides(rows, ["nvd:ceo=1", "ORCL:ceo=0", "ORCL:debt=0"])
    assert rows[0]["scores"]["ceo"] == 1 and rows[0]["set"] == {"ceo": 1}
    assert rows[0]["total"] == 2 + 1 + 1 + 2 + 1
    assert rows[1]["total"] == 2 + 1 + 0 + 0 + 1


@pytest.mark.parametrize("bad", ["ORCL:moat=1", "ORCL:ceo=3", "ORCL ceo 1", "XYZ:ceo=2"])
def test_override_refuses_an_unknown_factor_point_form_or_ticker(bad):
    with pytest.raises(ValueError):
        q.apply_overrides([_row("ORCL")], [bad])


# --- Yahoo quoteSummary parse ---------------------------------------------------------------------

def _raw(v):
    return {"raw": v, "fmt": str(v)}


SUMMARY = {
    "financialData": {
        "currentPrice": _raw(346.65), "targetMedianPrice": _raw(525.0), "recommendationKey": "strong_buy",
        "recommendationMean": _raw(1.27), "numberOfAnalystOpinions": _raw(47), "totalDebt": _raw(59.4e9),
        "totalCash": _raw(24.0e9), "ebitda": _raw(52.3e9), "freeCashflow": _raw(30.6e9),
        "revenueGrowth": _raw(0.855),
    },
    "summaryDetail": {"forwardPE": _raw(17.88), "marketCap": _raw(1.65e12)},
    "defaultKeyStatistics": {"enterpriseToRevenue": _raw(18.97)},
    "calendarEvents": {"earnings": {"earningsDate": [{"raw": 1796850000, "fmt": "2026-12-09"}]}},
    "earningsTrend": {"trend": [
        {"period": "0y", "growth": _raw(0.71), "epsTrend": {"current": _raw(11.66), "90daysAgo": _raw(11.63)}},
        {"period": "+1y", "growth": _raw(0.662), "epsTrend": {"current": _raw(19.386), "90daysAgo": _raw(19.5369)}},
    ]},
}


def test_parse_summary_flattens_the_fields_the_scores_need():
    f = q.parse_summary(SUMMARY)
    assert f["target_median"] == 525.0
    assert f["rating"] == "strong_buy" and f["n_analysts"] == 47
    assert f["fpe"] == 17.88 and f["ev_sales"] == 18.97
    assert f["eps_growth"] == 0.662 and f["eps_now"] == 19.386 and f["eps_90d"] == 19.5369
    assert f["debt"] == 59.4e9 and f["cash"] == 24.0e9 and f["ebitda"] == 52.3e9 and f["fcf"] == 30.6e9
    assert f["next_earnings"] == "2026-12-09"


def test_parse_summary_tolerates_missing_modules():
    f = q.parse_summary({})
    assert f["fpe"] is None and f["next_earnings"] is None and f["rating"] is None


def _ts(typ, pts):
    return {"meta": {"type": [typ]}, typ: [{"asOfDate": d, "reportedValue": {"raw": v}} for d, v in pts]}


TIMESERIES = {"timeseries": {"result": [
    _ts("annualTotalRevenue", [("2023-12-31", 100.0), ("2024-12-31", 120.0), ("2025-12-31", 150.0)]),
    _ts("annualEBITDA", [("2023-12-31", 30.0), ("2024-12-31", 30.0), ("2025-12-31", 45.0)]),
    _ts("annualResearchAndDevelopment", [("2023-12-31", 25.0), ("2024-12-31", 30.0), ("2025-12-31", 30.0)]),
    _ts("annualFreeCashFlow", [("2024-12-31", 9.0), ("2025-12-31", 12.0)]),
    _ts("trailingTotalRevenue", [("2026-09-30", 200.0)]),
    _ts("trailingEBITDA", [("2026-09-30", 70.0)]),
    _ts("trailingResearchAndDevelopment", [("2026-09-30", 38.0)]),
    _ts("trailingFreeCashFlow", [("2026-09-30", -4.0)]),
]}}


def test_parse_timeseries_keeps_fiscal_years_and_the_latest_12_months():
    acc = q.parse_timeseries(TIMESERIES)
    assert acc["rev"]["2025-12-31"] == 150.0 and acc["rd"]["2023-12-31"] == 25.0
    assert acc["ttm"] == {"rev": 200.0, "ebitda": 70.0, "rd": 38.0, "fcf": -4.0, "date": "2026-09-30"}
    assert acc["fcf"] == -4.0


def test_scores_from_accounts_and_a_parsed_summary():
    f = q.parse_summary(SUMMARY)                      # Broadcom-like: 0.68 years of net debt, +-0.8% estimate
    s = q.scores(f, q.parse_timeseries(TIMESERIES))   # windows 2024, 2025, latest 12 months
    # EBITDA 25/30/35% -> 2; R&D 25/20/19% -> average 21.3% -> 1; free cash flow -4 -> debt 1
    assert s == {"cash": 2, "tech": 1, "ceo": None, "debt": 1, "outlook": 1}


def test_markdown_ranks_rows_and_marks_hand_set_values():
    a = _row("AAA", fpe=28.0) | {"total": 7, "price": 10.0, "currency": "USD"}
    b = _row("BBB", fpe=9.0) | {"total": 7, "price": 20.0, "currency": "USD"}
    b["scores"]["ceo"], b["set"] = 1, {"ceo": 1}
    lines = q.to_markdown([a, b]).splitlines()
    assert lines[2].startswith("| BBB") and lines[3].startswith("| AAA")
    assert "| 1* |" in lines[2]


def test_parse_summary_reads_the_reporting_currency():
    f = q.parse_summary({"financialData": {"financialCurrency": "TWD"}})
    assert f["report_ccy"] == "TWD"


def test_a_row_reporting_in_another_currency_loses_its_sales_multiple_and_is_marked():
    f = {"report_ccy": "TWD", "ev_sales": 2.4, "fpe": 15.1}
    assert q.currency_guard(f, "USD") == {"report_ccy": "TWD", "ev_sales": None, "fpe": 15.1, "fx": True}
    assert q.currency_guard({"report_ccy": "KRW", "ev_sales": 1.8}, "KRW")["fx"] is False
    row = _row("TSM") | {"total": 8, "price": 352.0, "currency": "USD", "fx": True}
    assert q.to_markdown([row]).splitlines()[2].startswith("| TSM †")
