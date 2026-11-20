#!/usr/bin/env python3
"""Price, trend, analyst and balance-sheet data from Yahoo Finance, scored under the risk-first weights.

    quotes.py TICKER [TICKER ...] [--set TICKER:factor=score ...] [--json OUT.json]

A ticker may be a German listing of a US stock (NVD, FB2A or NVD.DE): the analysis runs on the US
listing and the row also shows the German price in its own currency. The script prints one
Markdown table sorted by score. Each factor is scored 1 to 5, 5 the best; the weighted total runs from
20 to 100. Four factors are computed here; catalysts is set by hand (`--set NVDA:catalysts=4`) and stays
a neutral 3 until then. `--set` also overrides a computed factor when research finds what the numbers
miss, such as leases outside reported debt. Hand-set values carry a `*` in the table.

Standard library and curl. In Claude Code the command needs network access to fc.yahoo.com and
query1.finance.yahoo.com.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
import time
from datetime import date

WEIGHTS = {"financing": 35, "growth": 25, "valuation": 20, "catalysts": 10, "trend": 10}
FACTORS = tuple(WEIGHTS)

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
        return {"price": None, "r1m": None, "r3m": None, "ma200": None}
    price = c[-1]
    return {
        "price": price,
        "r1m": price / c[-22] - 1 if len(c) >= 22 else None,
        "r3m": price / c[-64] - 1 if len(c) >= 64 else None,
        "ma200": sum(c[-200:]) / 200 if len(c) >= 200 else None,
    }


# --- factor scores, 5 is best ---------------------------------------------------------------------

def _clamp(x: int) -> int:
    return max(1, min(5, x))


def score_financing(debt, cash, ebitda, fcf) -> int | None:
    """Net debt against EBITDA; burning cash costs a point."""
    if debt is None and cash is None:
        return None
    net = (debt or 0) - (cash or 0)
    if net <= 0:
        s = 5
    elif not ebitda or ebitda <= 0:
        s = 1
    else:
        lev = net / ebitda
        s = 4 if lev < 1 else 3 if lev < 2.5 else 2 if lev < 4 else 1
    if fcf is not None and fcf < 0:
        s -= 1
    return _clamp(s)


def score_growth(rev_growth, eps_now, eps_90d) -> int | None:
    """Revenue growth over the year, moved a point by a 5% change in next year's earnings estimate."""
    if rev_growth is None:
        return None
    g = rev_growth
    s = 5 if g > 0.5 else 4 if g > 0.25 else 3 if g > 0.10 else 2 if g > 0 else 1
    if eps_now is not None and eps_90d:
        rev = (eps_now - eps_90d) / abs(eps_90d)
        s += 1 if rev > 0.05 else -1 if rev < -0.05 else 0
    return _clamp(s)


GROWTH_CAP = 0.5   # next year's earnings growth counted at most 50%: higher growth from a small base misleads
RICH_SALES = 20    # above 20 times sales, valuation scores at most 2


def score_valuation(fpe, eps_growth, ev_sales) -> int | None:
    """Forward P/E against next year's earnings growth (capped); P/E alone without growth; EV/sales for a
    loss-maker. A price above 20 times sales scores at most 2 whatever the earnings say."""
    if fpe is not None and fpe > 0:
        if eps_growth is not None and eps_growth > 0:
            peg = fpe / (min(eps_growth, GROWTH_CAP) * 100)
            s = 5 if peg < 0.8 else 4 if peg < 1.2 else 3 if peg < 1.8 else 2 if peg < 2.5 else 1
        else:
            s = 4 if fpe < 12 else 3 if fpe < 20 else 2 if fpe < 30 else 1
    elif ev_sales is None:
        return None
    else:
        s = 4 if ev_sales < 3 else 3 if ev_sales < 6 else 2 if ev_sales < 12 else 1
    if ev_sales is not None and ev_sales > RICH_SALES:
        s = min(s, 2)
    return s


def earnings_label(when: str | None, today: date | None = None) -> str:
    """The next earnings date, or "reported <date>" when Yahoo still carries one already past."""
    if not when:
        return "n/a"
    return when if when >= (today or date.today()).isoformat() else f"reported {when}"


def score_trend(r3m, price, ma200) -> int | None:
    """Three-month return and the price against its 200-day average."""
    if r3m is None:
        return None
    if ma200 is None:
        return 4 if r3m > 0.10 else 3 if r3m >= 0 else 2 if r3m > -0.20 else 1
    above = price is not None and price > ma200
    if above:
        return 5 if r3m > 0.10 else 4 if r3m >= 0 else 3
    return 3 if r3m >= 0 else 2 if r3m > -0.20 else 1


def scores(f: dict, r: dict) -> dict:
    return {
        "financing": score_financing(f.get("debt"), f.get("cash"), f.get("ebitda"), f.get("fcf")),
        "growth": score_growth(f.get("rev_growth"), f.get("eps_now"), f.get("eps_90d")),
        "valuation": score_valuation(f.get("fpe"), f.get("eps_growth"), f.get("ev_sales")),
        "trend": score_trend(r.get("r3m"), r.get("price"), r.get("ma200")),
    }


def total(s: dict) -> float | None:
    full = {k: s.get(k) for k in FACTORS}
    if full["catalysts"] is None:
        full["catalysts"] = 3
    if any(v is None for v in full.values()):
        return None
    return round(sum(WEIGHTS[k] * v for k, v in full.items()) / 5, 1)


_SET = re.compile(r"^([A-Za-z0-9.\-]+):([a-z]+)=([1-5])$")


def apply_overrides(rows: list[dict], sets: list[str]) -> list[dict]:
    for item in sets:
        m = _SET.match(item.strip())
        if not m:
            raise ValueError(f"--set wants TICKER:factor=1..5, got {item!r}")
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
        r = returns(ch["closes"])
        row = {**r, **f, "ticker": tick, "held": held, "name": f["name"] or ch["meta"].get("longName"),
               "currency": ch["meta"].get("currency"), "scores": scores(f, r), "set": {}}
        row["price"] = r["price"] or ch["meta"].get("regularMarketPrice")
        row["high52"] = ch["meta"].get("fiftyTwoWeekHigh")
        row["low52"] = ch["meta"].get("fiftyTwoWeekLow")
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
    if k == "catalysts" and v is None:
        return "3?"
    return ("n/a" if v is None else str(v)) + ("*" if k in row.get("set", {}) else "")


def to_markdown(rows: list[dict]) -> str:
    head = ("| Stock | Price | 3 mo | vs 200-day | Street | Target | Financing | Growth | Valuation "
            "| Catalysts | Trend | Score | Earnings |")
    out = [head, "|" + "---|" * 13]
    for r in sorted(rows, key=lambda r: (r.get("total") is None, -(r.get("total") or 0))):
        stock = r["ticker"] + (" †" if r.get("fx") else "") + (f" ({r['held']})" if r.get("held") else "")
        price = f"{_num(r.get('price'), 2)} {r.get('currency') or ''}".strip()
        if r.get("held_price") is not None:
            price += f" / {r['held_price']:.2f} {r.get('held_currency') or ''}".rstrip()
        ma = r.get("ma200")
        vs = "n/a" if ma is None or r.get("price") is None else _pct(r["price"] / ma - 1)
        street = f"{(r.get('rating') or 'n/a').replace('_', ' ')} ({r.get('n_analysts') or 0})"
        target = "n/a" if r.get("target_median") is None else f"{r['target_median']:.0f} ({_pct(r.get('upside'))})"
        cells = [stock, price, _pct(r.get("r3m")), vs, street, target,
                 *(_s(r, k) for k in ("financing", "growth", "valuation", "catalysts", "trend")),
                 _num(r.get("total")), earnings_label(r.get("next_earnings"))]
        out.append("| " + " | ".join(cells) + " |")
    if any(r.get("fx") for r in rows):
        out.append("\n† reports in another currency than it trades in: Yahoo's sales multiple is dropped; "
                   "check the valuation at a second source.")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("tickers", nargs="+")
    ap.add_argument("--set", action="append", default=[], metavar="TICKER:factor=score")
    ap.add_argument("--json", metavar="OUT.json", help="write every fetched field and score to this file")
    a = ap.parse_args(argv)
    rows = fetch(a.tickers)
    try:
        apply_overrides(rows, a.set)
    except ValueError as e:
        print(f"quotes.py: {e}", file=sys.stderr)
        return 2
    print(f"Yahoo Finance, fetched {date.today().isoformat()}; weights "
          + ", ".join(f"{k} {w}" for k, w in WEIGHTS.items()) + "\n")
    print(to_markdown(rows))
    if a.json:
        with open(a.json, "w") as fh:
            json.dump(rows, fh, indent=1, default=str)
    return 0


if __name__ == "__main__":
    sys.exit(main())
