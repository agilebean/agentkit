"""The stock-analysis skill's data script (skills/stock-analysis/scripts/quotes.py).

Covers the parts that decide a score: the listing a ticker resolves to, the price returns, the four
mechanical factor scores under the risk-first weights, the hand-set overrides, and the parse of a Yahoo
quoteSummary result. No test here touches the network.
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


# --- factor scores (5 is best) --------------------------------------------------------------------

@pytest.mark.parametrize("debt,cash,ebitda,fcf,expected", [
    (10, 20, 5, 1, 5),          # net cash
    (5, 20, -3, -2, 4),         # net cash, cash burn costs a point
    (59.4, 24.0, 52.3, 30.6, 4),  # net debt 0.68x EBITDA
    (100, 10, 50, 5, 3),        # 1.8x
    (100, 10, 30, 5, 2),        # 3.0x
    (100, 10, 30, -5, 1),       # 3.0x and burning cash
    (100, 10, 15, 5, 1),        # 6.0x
    (100, 10, -5, -5, 1),       # net debt, no EBITDA
    (100, 10, None, None, 1),
    (None, None, None, None, None),
])
def test_financing_score(debt, cash, ebitda, fcf, expected):
    assert q.score_financing(debt, cash, ebitda, fcf) == expected


@pytest.mark.parametrize("rev,eps_now,eps_90d,expected", [
    (0.855, 19.386, 19.5369, 5),   # revisions -0.8%: no change
    (0.30, 2.2, 2.0, 5),           # 4, raised 10%: +1
    (0.05, 1.0, 1.2, 1),           # 2, cut 17%: -1
    (-0.10, None, None, 1),
    (0.15, -1.0, -2.0, 4),         # loss narrowing counts as a raise
    (None, 1.0, 1.0, None),
])
def test_growth_score(rev, eps_now, eps_90d, expected):
    assert q.score_growth(rev, eps_now, eps_90d) == expected


@pytest.mark.parametrize("fpe,growth,ev_sales,expected", [
    (17.88, 0.662, 18.97, 5),   # growth-adjusted P/E 0.27
    (25, 0.25, 8, 4),           # 1.0
    (30, 0.20, 8, 3),           # 1.5
    (40, 0.20, 10, 2),          # 2.0
    (60, 0.20, 10, 1),          # 3.0
    (30, -0.10, 5, 1),          # no growth: P/E alone
    (11, None, 5, 4),
    (None, None, 5, 3),         # loss-making: EV/sales, capped at 4
    (-12, 0.5, 2, 4),
    (None, None, 20, 1),
    (None, None, None, None),
])
def test_valuation_score(fpe, growth, ev_sales, expected):
    assert q.score_valuation(fpe, growth, ev_sales) == expected


@pytest.mark.parametrize("fpe,growth,ev_sales,expected", [
    (50.49, 14.92, 57.09, 2),   # SPCX 2026-11-20: 1492% growth from a small base, 57 times sales
    (53.37, 1.16, 18.43, 4),    # IREN: growth capped at 50%, so P/E 53 is no bargain
    (57.39, 0.36, 34.12, 2),    # ARM: above 20 times sales
    (27.73, 1.18, 17.51, 5),    # AMD
])
def test_valuation_caps_growth_at_50_percent_and_scores_above_20_times_sales_at_most_2(
        fpe, growth, ev_sales, expected):
    assert q.score_valuation(fpe, growth, ev_sales) == expected


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


@pytest.mark.parametrize("pe_chg,eps_rev,ev_sales,expected", [
    (-0.40, 0.00, 5, 4),    # P/E down 40% on an estimate that held: one point cheaper than the level says
    (-0.20, 0.00, 5, 3),    # down 20%: not enough
    (-0.40, -0.10, 5, 3),   # estimate cut 10%: the price followed the earnings down, not cheaper
    (None, None, 5, 3),
    (-0.40, 0.00, 25, 2),   # above 20 times sales the cap still holds
])
def test_valuation_rises_one_when_the_pe_fell_30_percent_on_an_estimate_that_held(
        pe_chg, eps_rev, ev_sales, expected):
    assert q.score_valuation(30, 0.20, ev_sales, pe_chg, eps_rev) == expected   # level alone: 3


def test_scores_pass_the_pe_change_to_valuation():
    f = {"fpe": 30, "eps_growth": 0.20, "ev_sales": 5, "eps_now": 2.0, "eps_90d": 2.0}
    r = {"price": 60.0, "p3m": 100.0, "r3m": -0.4, "ma200": 90.0}
    assert q.scores(f, r)["valuation"] == 4


@pytest.mark.parametrize("when,expected", [
    ("2026-12-09", "2026-12-09"),
    ("2026-11-20", "2026-11-20"),
    ("2026-11-17", "reported 2026-11-17"),
    (None, "n/a"),
])
def test_earnings_label_marks_a_date_already_past(when, expected):
    from datetime import date
    assert q.earnings_label(when, today=date(2026, 11, 20)) == expected


@pytest.mark.parametrize("r3m,price,ma200,expected", [
    (0.15, 110, 100, 5),
    (0.05, 110, 100, 4),
    (-0.05, 110, 100, 3),
    (0.05, 90, 100, 3),
    (-0.10, 90, 100, 2),
    (-0.30, 90, 100, 1),
    (0.15, 100, None, 4),       # young listing: no 200-day average, capped at 4
    (-0.30, 100, None, 1),
    (None, 100, 100, None),
])
def test_trend_score(r3m, price, ma200, expected):
    assert q.score_trend(r3m, price, ma200) == expected


# --- weighted total -------------------------------------------------------------------------------

def test_weights_are_risk_first_and_sum_to_100():
    assert q.WEIGHTS == {"financing": 35, "growth": 25, "valuation": 20, "catalysts": 10, "trend": 10}


def test_total_runs_from_20_to_100():
    five = dict.fromkeys(q.WEIGHTS, 5)
    one = dict.fromkeys(q.WEIGHTS, 1)
    assert q.total(five) == 100.0
    assert q.total(one) == 20.0


def test_total_takes_neutral_catalysts_until_they_are_set_and_none_when_a_factor_is_missing():
    s = {"financing": 5, "growth": 5, "valuation": 5, "trend": 5}
    assert q.total(s) == 100.0 - 10 * 2 / 5
    assert q.total(s | {"growth": None}) is None


# --- overrides ------------------------------------------------------------------------------------

def _row(t, **scores):
    base = {"financing": 3, "growth": 3, "valuation": 3, "trend": 3}
    return {"ticker": t, "held": None, "scores": base | scores, "set": {}}


def test_override_sets_a_factor_by_either_listing_and_recomputes_the_total():
    rows = [_row("NVDA"), _row("ORCL")]
    rows[0]["held"] = "NVD.DE"
    q.apply_overrides(rows, ["nvd:catalysts=5", "ORCL:financing=1"])
    assert rows[0]["scores"]["catalysts"] == 5 and rows[0]["set"] == {"catalysts": 5}
    assert rows[1]["scores"]["financing"] == 1
    assert rows[1]["total"] == q.total(rows[1]["scores"])


@pytest.mark.parametrize("bad", ["ORCL:moat=3", "ORCL:financing=6", "ORCL financing 1", "XYZ:trend=2"])
def test_override_refuses_an_unknown_factor_score_form_or_ticker(bad):
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


def test_scores_from_a_parsed_summary_and_returns():
    f = q.parse_summary(SUMMARY)
    s = q.scores(f, {"price": 346.65, "r3m": 0.12, "ma200": 300.0})
    assert s == {"financing": 4, "growth": 5, "valuation": 5, "trend": 5}


def test_markdown_sorts_by_total_and_marks_hand_set_factors():
    a = _row("AAA", financing=5) | {"total": 70.0, "price": 10.0, "currency": "USD"}
    b = _row("BBB") | {"total": 60.0, "price": 20.0, "currency": "USD"}
    b["scores"]["catalysts"] = 4
    b["set"] = {"catalysts": 4}
    md = q.to_markdown([b, a])
    lines = md.splitlines()
    assert lines[2].startswith("| AAA") and lines[3].startswith("| BBB")
    assert "4*" in lines[3]


def test_parse_summary_reads_the_reporting_currency():
    f = q.parse_summary({"financialData": {"financialCurrency": "TWD"}})
    assert f["report_ccy"] == "TWD"


def test_a_row_reporting_in_another_currency_loses_its_sales_multiple_and_is_marked():
    f = {"report_ccy": "TWD", "ev_sales": 2.4, "fpe": 15.1}
    assert q.currency_guard(f, "USD") == {"report_ccy": "TWD", "ev_sales": None, "fpe": 15.1, "fx": True}
    assert q.currency_guard({"report_ccy": "KRW", "ev_sales": 1.8}, "KRW")["fx"] is False
    row = _row("TSM") | {"total": 80.0, "price": 352.0, "currency": "USD", "fx": True}
    assert q.to_markdown([row]).splitlines()[2].startswith("| TSM †")
