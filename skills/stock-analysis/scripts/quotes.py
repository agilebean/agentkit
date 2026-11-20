#!/usr/bin/env python3
"""Price, earnings and three years of accounts from Yahoo Finance, scored on five factors of 0-2 points.

    quotes.py TICKER [TICKER ...] [--set TICKER:factor=points ...] [--json OUT.json]

Score = Cash + Tech + CEO + Debt + Outlook, each 0, 1 or 2 points (10 the best); equal scores rank by
the lower forward P/E. Cash is EBITDA over revenue and Tech is research and development (R&D) over
revenue, each 2 when above 20% in every one of the last three years and 1 when above 20% on their
average. Debt is 2 for net debt under one year of EBITDA with positive free cash flow, 1 when one of the
two fails or net debt runs 1-3 years of EBITDA, 0 above 3 years or with no EBITDA. Outlook is next
year's earnings estimate against 90 days ago: up 5% or more 2, within 5% 1, cut more or a loss 0. CEO
is set by hand (`--set NVDA:ceo=1`): excellent 2, good 1, weak 0; a row without it has no score.

A ticker may be a German listing of a US stock (NVD, FB2A or NVD.DE): the analysis runs on the US
listing and the row also shows the German price in its own currency. Hand-set values carry a `*`.

Standard library and curl. In Claude Code the command needs network access to fc.yahoo.com and
query1.finance.yahoo.com.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
import tempfile
import time
from datetime import date

FACTORS = ("cash", "tech", "ceo", "debt", "outlook")
BAR = 0.20          # Cash and Tech: the share of revenue that passes
TTM_AFTER = 180     # days: the latest 12 months replace the oldest year once they end this long after it

# German listing -> (US listing for the analysis, the German listing as Yahoo names it).
LISTINGS = {"NVD": ("NVDA", "NVD.DE"), "FB2A": ("META", "FB2A.DE")}

MODULES = "financialData,summaryDetail,defaultKeyStatistics,calendarEvents,earningsTrend,price"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"


# --- listings and returns -------------------------------------------------------------------------

def resolve(ticker: str) -> tuple[str, str | None]:
    t = ticker.strip().upper()
    base = t[:-3] if t.endswith(".DE") else t
    if base in LISTINGS:
        return LISTINGS[base]
    return t, None


def returns(closes: list[float | None]) -> dict:
    c = [x for x in closes if x is not None]
    if not c:
        return {"price": None, "r1m": None, "r3m": None, "ma200": None, "p3m": None, "high": None,
                "from_high": None}
    price = c[-1]
    return {
        "price": price,
        "r1m": price / c[-22] - 1 if len(c) >= 22 else None,
        "r3m": price / c[-64] - 1 if len(c) >= 64 else None,
        "ma200": sum(c[-200:]) / 200 if len(c) >= 200 else None,
        "p3m": c[-64] if len(c) >= 64 else None,
        "high": max(c),
        "from_high": price / max(c) - 1,
    }


def pe_change(price, p3m, eps_now, eps_90d) -> float | None:
    """How far the forward P/E moved in 3 months: the price move divided by the move in next year's
    earnings estimate. The currencies cancel, so it holds for a stock that reports in another one."""
    if None in (price, p3m, eps_now, eps_90d) or p3m <= 0 or eps_now <= 0 or eps_90d <= 0:
        return None
    return (price / p3m) / (eps_now / eps_90d) - 1


# --- the five factors, each 0-2 points -----------------------------------------------------------

def windows(annual_dates: list[str], ttm_date: str | None) -> list[str]:
    """The three yearly windows: the last three fiscal years, or the last two and the latest 12 months
    ("ttm") once those end at least half a year after the last fiscal year."""
    ys = sorted(annual_dates)[-3:]
    if ttm_date and ys and (date.fromisoformat(ttm_date) - date.fromisoformat(ys[-1])).days >= TTM_AFTER:
        return ys[-2:] + ["ttm"]
    return ys


def shares(rev: dict, part: dict, wins: list[str], missing_zero: bool = False) -> list[float] | None:
    """part over revenue in each window. A company that reports no R&D at all counts 0 (missing_zero);
    otherwise a gap leaves no figure."""
    if not wins or (not part and not missing_zero):
        return None
    out = []
    for w in wins:
        r = rev.get(w)
        if not r or r <= 0:
            return None
        v = part.get(w)
        if v is None and not missing_zero:
            return None
        out.append((v or 0.0) / r)
    return out


def score_three_years(ratios: list[float] | None, bar: float = BAR) -> int | None:
    """2 when above the bar in every year, 1 when above it on the average, 0 below."""
    if not ratios:
        return None
    if all(x > bar for x in ratios):
        return 2
    return 1 if sum(ratios) / len(ratios) > bar else 0


def net_debt_years(debt, cash, ebitda) -> float | None:
    """Net debt in years of EBITDA; negative for net cash, inf when net debt meets no EBITDA."""
    if debt is None and cash is None:
        return None
    net = (debt or 0) - (cash or 0)
    if net <= 0:
        return net / ebitda if ebitda and ebitda > 0 else -math.inf
    return net / ebitda if ebitda and ebitda > 0 else math.inf


def score_debt(years: float | None, fcf) -> int | None:
    """2: net debt under one year of EBITDA and free cash flow not negative. One year to three, or
    negative free cash flow, costs a point each. Above three years, or net debt with no EBITDA: 0."""
    if years is None:
        return None
    if years > 3:
        return 0
    return max(0, 2 - (years > 1) - (fcf is not None and fcf < 0))


def eps_revision(eps_now, eps_90d) -> float | None:
    if eps_now is None or eps_90d is None or eps_90d <= 0:
        return None
    return eps_now / eps_90d - 1


def score_outlook(eps_now, eps_90d) -> int | None:
    """Next year's earnings estimate against 90 days ago: up 5% or more 2, within 5% 1, cut more 0.
    An estimate of a loss scores 0; one that turned from a loss to a profit scores 2."""
    if eps_now is None:
        return None
    if eps_now <= 0:
        return 0
    if eps_90d is None:
        return None
    if eps_90d <= 0:
        return 2
    rev = eps_now / eps_90d - 1
    return 2 if rev >= 0.05 else 1 if rev >= -0.05 else 0


def earnings_label(when: str | None, today: date | None = None) -> str:
    """The next earnings date, or "reported <date>" when Yahoo still carries one already past."""
    if not when:
        return "n/a"
    return when if when >= (today or date.today()).isoformat() else f"reported {when}"


def scores(f: dict, acc: dict) -> dict:
    """The computed factors; CEO stays None until set by hand."""
    wins = windows(list(acc.get("rev", {})), (acc.get("ttm") or {}).get("date"))
    rev = acc.get("rev", {}) | ({"ttm": acc["ttm"]["rev"]} if acc.get("ttm", {}).get("rev") else {})
    ebitda = acc.get("ebitda", {}) | ({"ttm": acc["ttm"]["ebitda"]} if acc.get("ttm", {}).get("ebitda") is not None else {})
    rd = acc.get("rd", {}) | ({"ttm": acc["ttm"]["rd"]} if acc.get("ttm", {}).get("rd") is not None else {})
    return {
        "cash": score_three_years(shares(rev, ebitda, wins)),
        "tech": score_three_years(shares(rev, rd, wins, missing_zero=True)),
        "ceo": None,
        "debt": score_debt(net_debt_years(f.get("debt"), f.get("cash"), f.get("ebitda")), acc.get("fcf")),
        "outlook": score_outlook(f.get("eps_now"), f.get("eps_90d")),
    }


def total(s: dict) -> int | None:
    vals = [s.get(k) for k in FACTORS]
    return None if any(v is None for v in vals) else sum(vals)


def rank_key(row: dict) -> tuple:
    """Higher score first; equal scores by the lower forward P/E; a loss or no P/E last."""
    pe = row.get("fpe")
    return (row.get("total") is None, -(row.get("total") or 0), pe if pe and pe > 0 else math.inf)


_SET = re.compile(r"^([A-Za-z0-9.\-]+):([a-z]+)=([0-2])$")


def apply_overrides(rows: list[dict], sets: list[str]) -> list[dict]:
    for item in sets:
        m = _SET.match(item.strip())
        if not m:
            raise ValueError(f"--set wants TICKER:factor=0..2, got {item!r}")
        tick, factor, val = m.group(1), m.group(2), int(m.group(3))
        if factor not in FACTORS:
            raise ValueError(f"unknown factor {factor!r}; factors are {', '.join(FACTORS)}")
        want = resolve(tick)[0]
        hit = [r for r in rows if r["ticker"] == want]
        if not hit:
            raise ValueError(f"{tick} is not among the tickers fetched")
        for r in hit:
            r["scores"][factor] = val
            r["set"][factor] = val
    for r in rows:
        r["total"] = total(r["scores"])
    return rows


# --- Yahoo ----------------------------------------------------------------------------------------

def _v(d: dict | None, key: str):
    x = (d or {}).get(key)
    return x.get("raw") if isinstance(x, dict) else x


def parse_summary(res: dict) -> dict:
    fd = res.get("financialData") or {}
    sd = res.get("summaryDetail") or {}
    ks = res.get("defaultKeyStatistics") or {}
    dates = ((res.get("calendarEvents") or {}).get("earnings") or {}).get("earningsDate") or []
    nxt = next((t for t in (res.get("earningsTrend") or {}).get("trend", []) if t.get("period") == "+1y"), {})
    eps = nxt.get("epsTrend") or {}
    return {
        "name": _v(res.get("price"), "longName") or _v(res.get("price"), "shortName"),
        "report_ccy": _v(fd, "financialCurrency"),
        "target_median": _v(fd, "targetMedianPrice"),
        "rating": _v(fd, "recommendationKey"),
        "rec_mean": _v(fd, "recommendationMean"),
        "n_analysts": _v(fd, "numberOfAnalystOpinions"),
        "fpe": _v(sd, "forwardPE"),
        "ev_sales": _v(ks, "enterpriseToRevenue"),
        "market_cap": _v(sd, "marketCap"),
        "rev_growth": _v(fd, "revenueGrowth"),
        "eps_growth": _v(nxt, "growth"),
        "eps_now": _v(eps, "current"),
        "eps_90d": _v(eps, "90daysAgo"),
        "debt": _v(fd, "totalDebt"),
        "cash": _v(fd, "totalCash"),
        "ebitda": _v(fd, "ebitda"),
        "fcf": _v(fd, "freeCashflow"),
        "next_earnings": dates[0].get("fmt") if dates else None,
    }


TS_TYPES = {"TotalRevenue": "rev", "EBITDA": "ebitda", "ResearchAndDevelopment": "rd", "FreeCashFlow": "fcf"}


def parse_timeseries(d: dict) -> dict:
    """Yahoo's fundamentals timeseries into {"rev": {fiscal-year end: value}, "ebitda": ..., "rd": ...,
    "ttm": {"date": ..., "rev": ..., "ebitda": ..., "rd": ...}, "fcf": the latest 12 months' free cash
    flow, else the last fiscal year's}."""
    out: dict = {k: {} for k in TS_TYPES.values()} | {"ttm": {}}
    for res in (d.get("timeseries") or {}).get("result") or []:
        typ = ((res.get("meta") or {}).get("type") or [""])[0]
        for prefix in ("annual", "trailing"):
            if not typ.startswith(prefix) or typ[len(prefix):] not in TS_TYPES:
                continue
            key = TS_TYPES[typ[len(prefix):]]
            pts = [(v["asOfDate"], v["reportedValue"]["raw"]) for v in res.get(typ) or [] if v]
            if prefix == "annual":
                out[key] = dict(pts)
            elif pts:
                when, val = max(pts)
                out["ttm"][key] = val
                out["ttm"]["date"] = max(out["ttm"].get("date", ""), when)
    annual_fcf = out.pop("fcf")
    out["fcf"] = out["ttm"].get("fcf", annual_fcf[max(annual_fcf)] if annual_fcf else None)
    return out


def currency_guard(f: dict, trade_ccy: str | None) -> dict:
    """A company that reports in another currency than it trades in (TSM in TWD, BABA in CNY) gets an
    EV/sales from Yahoo that mixes the two (TSM 2.4, BABA 0.13 on 2026-11-20): drop it and mark the row,
    so its valuation is checked at a second source."""
    fx = bool(f.get("report_ccy") and trade_ccy and f["report_ccy"] != trade_ccy)
    return f | {"ev_sales": None if fx else f.get("ev_sales"), "fx": fx}


class Yahoo:
    """Yahoo Finance through curl. Python's urllib sends "Connection: close", and the Claude Code sandbox
    proxy then cuts long replies short (IncompleteRead, or 20256 of 28624 bytes); curl keeps the
    connection open and gets every reply whole (2026-11-20)."""

    def __init__(self) -> None:
        self.jar = tempfile.NamedTemporaryFile(prefix="yahoo-", suffix=".cookies", delete=False).name
        self._get("https://fc.yahoo.com")  # sets the session cookie, answers 404
        self.crumb = self._get("https://query1.finance.yahoo.com/v1/test/getcrumb").decode().strip()
        if not self.crumb or "<" in self.crumb:
            raise RuntimeError("Yahoo gave no crumb; the cookie request failed")

    def _get(self, url: str) -> bytes:
        cmd = ["curl", "-s", "-m", "20", "--compressed", "-A", UA, "-b", self.jar, "-c", self.jar, url]
        return subprocess.run(cmd, capture_output=True, check=False).stdout

    def _json(self, url: str) -> dict:
        err = "no reply"
        for wait in (0, 2, 5):
            time.sleep(wait)
            body = self._get(url)
            try:
                return json.loads(body)
            except ValueError as e:
                err = f"{e} ({len(body)} bytes)"
        raise RuntimeError(f"{url}: {err}")

    def chart(self, t: str) -> dict:
        d = self._json(f"https://query1.finance.yahoo.com/v8/finance/chart/{t}?range=1y&interval=1d")
        res = (d.get("chart") or {}).get("result") or []
        if not res:
            return {"closes": [], "meta": {}}
        r = res[0]
        closes = (((r.get("indicators") or {}).get("quote") or [{}])[0]).get("close") or []
        return {"closes": closes, "meta": r.get("meta") or {}}

    def accounts(self, t: str) -> dict:
        types = ",".join(p + k for p in ("annual", "trailing") for k in TS_TYPES)
        now = int(time.time())
        return parse_timeseries(self._json(
            "https://query1.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/timeseries/"
            f"{t}?type={types}&period1={now - 6 * 365 * 86400}&period2={now}"))

    def summary(self, t: str) -> dict:
        d = self._json(f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{t}"
                       f"?modules={MODULES}&crumb={self.crumb}")
        res = (d.get("quoteSummary") or {}).get("result") or []
        return res[0] if res else {}


def fetch(tickers: list[str]) -> list[dict]:
    y = Yahoo()
    rows, seen = [], set()
    for given in tickers:
        tick, held = resolve(given)
        if tick in seen:
            continue
        seen.add(tick)
        ch = y.chart(tick)
        f = currency_guard(parse_summary(y.summary(tick)), ch["meta"].get("currency"))
        acc = y.accounts(tick)
        r = returns(ch["closes"])
        row = {**r, **f, "ticker": tick, "held": held, "name": f["name"] or ch["meta"].get("longName"),
               "currency": ch["meta"].get("currency"), "accounts": acc, "scores": scores(f, acc), "set": {}}
        row["price"] = r["price"] or ch["meta"].get("regularMarketPrice")
        wins = windows(list(acc["rev"]), acc["ttm"].get("date"))
        rev = acc["rev"] | ({"ttm": acc["ttm"]["rev"]} if acc["ttm"].get("rev") else {})
        row["windows"] = wins
        row["ebitda_share"] = shares(rev, acc["ebitda"] | ({"ttm": acc["ttm"]["ebitda"]} if "ebitda" in acc["ttm"] else {}), wins)
        row["rd_share"] = shares(rev, acc["rd"] | ({"ttm": acc["ttm"]["rd"]} if "rd" in acc["ttm"] else {}), wins, missing_zero=True)
        row["debt_years"] = net_debt_years(f["debt"], f["cash"], f["ebitda"])
        row["pe_chg"] = pe_change(row["price"], r["p3m"], f["eps_now"], f["eps_90d"])
        row["eps_rev"] = eps_revision(f["eps_now"], f["eps_90d"])
        row["upside"] = (f["target_median"] / row["price"] - 1) if f["target_median"] and row["price"] else None
        if held:
            hm = y.chart(held)["meta"]
            row["held_price"], row["held_currency"] = hm.get("regularMarketPrice"), hm.get("currency")
        row["total"] = total(row["scores"])
        rows.append(row)
    return rows


# --- output ---------------------------------------------------------------------------------------

def _pct(x) -> str:
    return "n/a" if x is None else f"{x * 100:+.0f}%"


def _num(x, nd=1) -> str:
    return "n/a" if x is None else f"{x:.{nd}f}"


def _s(row: dict, k: str) -> str:
    v = row["scores"].get(k)
    return ("?" if v is None else str(v)) + ("*" if k in row.get("set", {}) else "")


def _shares(x: list[float] | None) -> str:
    return "n/a" if not x else "/".join(f"{v * 100:.0f}" for v in x) + "%"


def _years(x: float | None) -> str:
    if x is None:
        return "n/a"
    if x == math.inf:
        return "no EBITDA"
    return "net cash" if x <= 0 else f"{x:.1f}"


def to_markdown(rows: list[dict]) -> str:
    head = ("| Stock | Price | From high | P/E (3 mo ago) | EBITDA ÷ revenue | R&D ÷ revenue | Net debt, years "
            "of EBITDA | Free cash flow | Estimate 3 mo | Cash | Tech | CEO | Debt | Outlook | Score | Earnings |")
    out = [head, "|" + "---|" * 16]
    for r in sorted(rows, key=rank_key):
        stock = r["ticker"] + (" †" if r.get("fx") else "") + (f" ({r['held']})" if r.get("held") else "")
        price = f"{_num(r.get('price'), 2)} {r.get('currency') or ''}".strip()
        if r.get("held_price") is not None:
            price += f" / {r['held_price']:.2f} {r.get('held_currency') or ''}".rstrip()
        fpe, chg = r.get("fpe"), r.get("pe_chg")
        pe = "loss" if fpe is not None and fpe <= 0 else _num(fpe)
        if fpe and fpe > 0 and chg is not None:
            pe += f" ({fpe / (1 + chg):.1f})"
        fcf = (r.get("accounts") or {}).get("fcf")
        cells = [stock, price, _pct(r.get("from_high")), pe, _shares(r.get("ebitda_share")),
                 _shares(r.get("rd_share")), _years(r.get("debt_years")),
                 "n/a" if fcf is None else ("positive" if fcf >= 0 else "negative"), _pct(r.get("eps_rev")),
                 *(_s(r, k) for k in FACTORS), "?" if r.get("total") is None else str(r["total"]),
                 earnings_label(r.get("next_earnings"))]
        out.append("| " + " | ".join(cells) + " |")
    if any(r.get("fx") for r in rows):
        out.append("\n† reports in another currency than it trades in: check its P/E at a second source.")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("tickers", nargs="+")
    ap.add_argument("--set", action="append", default=[], metavar="TICKER:factor=points")
    ap.add_argument("--json", metavar="OUT.json", help="write every fetched field and score to this file")
    a = ap.parse_args(argv)
    rows = fetch(a.tickers)
    try:
        apply_overrides(rows, a.set)
    except ValueError as e:
        print(f"quotes.py: {e}", file=sys.stderr)
        return 2
    print(f"Yahoo Finance, fetched {date.today().isoformat()}. Score = Cash + Tech + CEO + Debt + Outlook, "
          "each 0-2; equal scores by the lower P/E\n")
    print(to_markdown(rows))
    if a.json:
        with open(a.json, "w") as fh:
            json.dump(rows, fh, indent=1, default=str)
    return 0


if __name__ == "__main__":
    sys.exit(main())
