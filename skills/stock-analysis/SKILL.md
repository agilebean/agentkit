---
name: stock-analysis
description: Analyze Chaehan's AI, semiconductor and robotics stocks for the next 3 months and the long term (3-5 years) - his holdings read against his recorded decisions, the candidates he names, and 3-5 new names the skill proposes - each scored under risk-first weights from Yahoo Finance data and checked research, written to a dated Hanji note "YYYY-MM-DD Stock Review" in the notebook Finance. Use when Chaehan asks to analyze, review or score his stocks or portfolio, asks whether to buy, sell or hold a stock, names tickers to look at, or asks for new stock ideas in AI, semiconductors or robotics.
---

# Stock analysis

What Chaehan gets: for every stock, where the evidence points over the next
3 months and over 3-5 years, the Wall Street consensus, a score from 20 to 100,
and the one fact that would reverse the reading. Holdings are read against the
decisions he recorded; candidates against what they would add to what he holds.

## The advice limit

The agent is not a licensed financial advisor and never writes buy, sell or hold
as its own call on Chaehan's money. It reports the evidence, the Street rating
labeled as the Street's, the score, and whether the facts since a decision
Chaehan recorded fit that decision or cut against it. When he asks for a
recommendation, say this once, in one sentence, and give everything up to the
decision. The decision and the order stay his.

## Inputs, read before any fetch

1. socrates `memory/stocks.md`: the holdings, the watchlist, every dated
   decision with its deadline and the reasons he gave, the tax-year rules, and
   what he recorded about where sale proceeds go (with its pointer into
   `memory/finance.md`). A new buy is read against that last rule.
2. The previous review: `$P search "Stock Review" --notebook Finance` (the hanji
   skill names `$H` and `$P`). The new note says what changed since.
3. A holdings list Chaehan gives in chat is the newest record: write it to the
   holdings line of `stocks.md` with the date in the same turn.

He names a stock by the ticker his broker shows. A German listing of a US
stock (NVD.DE for Nvidia) is analyzed on its US listing, with the German price
beside it; a new one goes into `LISTINGS` in `scripts/quotes.py` with a test.
SPCX is SpaceX Class A on Nasdaq (listed 2026-06-12), not the older SPAC ETF of
that ticker.

agentkit is a public repository, socrates a private one. Never write
Chaehan's positions, broker, decisions or amounts into this folder, its script
or its tests: they live in socrates `memory/stocks.md` and in the note.

## Steps

1. **Fetch and score** the holdings and named candidates, then the screen:

   ```
   Q="python3 $HOME/Software/Prototypes/agentkit/skills/stock-analysis/scripts/quotes.py"
   $Q arm avgo nvd ... intc amd --json $TMPDIR/stocks.json
   $Q <the universe in reference.md, minus the names above> --json $TMPDIR/screen.json
   ```

   In Claude Code each call names `allowed_domains`: `fc.yahoo.com`,
   `query1.finance.yahoo.com`. Eleven names take ~10 s, the universe ~30 s.
2. **Pick 3-5 new names** from the screen: the highest scores, at least one
   robotics name, ties broken by the largest rise in next
   year's earnings estimate over 90 days. A name he sold this year stays
   eligible and its row says he held it.
3. **Research every name** with web search (standard mode, several per turn),
   each fact with its date and source link:
   - the last quarter: date, revenue against the estimate, the guide;
   - catalysts dated inside the next 3 months: earnings, lockup expiry, index
     changes, launches, export rules, refinancing;
   - financing the balance sheet misses: leases, capex against market value,
     customer concentration, maturities;
   - the long-term case: what drives the company's growth for 3-5 years, and
     which event would end it;
   - the cause of the move when the 3-month return is beyond ±15%.

   Once per run: the sector's move and its cause, and the 10-year Treasury
   yield. A fact not read at its source is labeled unverified (RULES.md 244).
   A row marked † reports in another currency than it trades in: take its
   forward P/E from a second source.
4. **Set the hand factors** and rerun with `--set`: catalysts for every name
   (rubric in `reference.md`), and a financing or valuation override where
   research finds what the numbers miss. Each override gets a one-line reason
   in the note.
5. **Read each stock.** 3 months and long term, each Positive, Mixed or
   Negative with its decisive fact. A holding adds "Your plan": the recorded
   decision with its date, or "none recorded", and whether the facts since fit
   it. A candidate adds "Adds": what it brings that the holdings lack, or the
   overlap it deepens, and the first date that tests it.
6. **Write, check, file** (below).

## The note

Title `YYYY-MM-DD Stock Review`, notebook Finance, source file
`socrates/stocks/YYYY-MM-DD-stock-review.md`. A second run on the same day
rewrites that note; a new day makes a new note and leaves the earlier ones
untouched (RULES.md 31). Sections in this order:

1. **Summary**, three groups in this order, as Chaehan asked on 2026-11-20:
   Attractive (score 80 or more, the factors average 4 of 5), Mixed (60 to
   79), Sellable (below 60, under a neutral 3). Each group has two
   sub-bullets, Existing (his holdings) and New (his named candidates and the
   proposed names), and under them one line per stock, best case first: its
   score, the fact that puts it in the group, the fact that would move it out,
   its dated event inside 3 months, and for a holding whether the facts fit
   his recorded decision. An empty sub-bullet says so in one line; New under
   Sellable names the screened names below 60, marked unresearched. Nothing
   else goes in the Summary: the market, the yield and the method have their
   own sections. The groups rank the evidence and are not a call on his money
   (the advice limit); the Method section says so once.
2. **Holdings**, sorted by score: Stock, Why (what it sells into AI, one line),
   Score, 3 months, Long term, Street, Your plan.
3. **Candidates**, his named ones first, then the new ones marked "new": Stock,
   Why, Score, 3 months, Long term, Street, Adds.
4. **Scores**: the script's table and the hand-set lines (ticker, factor, value,
   reason).
5. **Per stock**, one `###` each: 3-6 dated facts with links.
6. **Method**: the weights, the data date, a pointer to `reference.md`.

Before the draft, read RULES.md's "The principle of parsimony" and rule 19
(line ranges in `rules.index.md`): a Summary line that places no stock in a
group moves to the section below. Wording follows `agentkit/AGENTS.md` core 1
and 4: spell out P/E, EV, HBM and every other abbreviation once; dates
YYYY-MM-DD; no thousand separators. Run
`python3 $HOME/Software/Prototypes/agentkit/scripts/wording_lint.py` on the file.

Filing: `$P create --notebook Finance --file <source>` (a same-day rewrite:
`$P write "<title>" --file <source> --base <sha>`), with the sandbox lifted for
that one command, then `$P get` to read it back. Update `stocks.md` (holdings,
the review's date and title under Current state), run `memory_lint.py` on it,
and commit the source file and `stocks.md` in socrates.
