---
name: stock-analysis
description: Analyze Chaehan's AI, semiconductor and robotics stocks - his holdings read against his recorded decisions, the candidates he names, and 3-5 new names the skill proposes - each scored 0-10 on five visible factors (EBITDA share of revenue, R&D share of revenue, CEO, debt, earnings outlook) with the forward P/E breaking ties, from Yahoo Finance data and checked research, written to a dated Hanji note "YYYY-MM-DD Stock Review" in the notebook Finance. Use when Chaehan asks to analyze, review or score his stocks or portfolio, asks whether to buy, sell or hold a stock, names tickers to look at, or asks for new stock ideas in AI, semiconductors or robotics.
---

# Stock analysis

What Chaehan gets: every stock placed as Attractive, Mixed or Sellable by a
score he can recompute from the table, its price against next year's earnings,
and the decisions due before the nearest deadline. Holdings are read against
the decisions he recorded; candidates against what they would add.

## The score

Score = Cash + Tech + CEO + Debt + Outlook, each 0, 1 or 2 points, 10 the best;
equal scores rank by the lower forward P/E (price over next year's earnings
estimate). Every factor is a column of the note's table, with its value and its
points; nothing else enters the score.

| Factor | 2 points | 1 point | 0 points |
|---|---|---|---|
| Cash: EBITDA ÷ revenue | above 20% in each of the three years | above 20% on their average | below |
| Tech: R&D ÷ revenue | above 20% in each of the three years | above 20% on their average | below, or no R&D reported |
| CEO: strategy and vision | excellent | good | weak |
| Debt: net debt in years of EBITDA, and free cash flow | under 1 year, cash flow positive | 1 to 3 years, or cash flow negative | above 3 years, both failing, or net debt with no EBITDA |
| Outlook: next year's earnings estimate against 90 days ago | up 5% or more, or turned from a loss to a profit | within 5% | cut more than 5%, or a loss expected |

The three years are the last two fiscal years and the latest 12 months, or the
last three fiscal years where those 12 months end less than half a year after
the last one. Groups: Attractive 8-10, Mixed 5-7, Sellable 0-4.

Cash, Tech and CEO are Chaehan's own criteria (2026-11-20). Debt and Outlook
are kept because they catch what his three miss: a company with a high EBITDA
share that borrows heavily or burns cash (EBITDA leaves out depreciation and
interest), and an earnings estimate cut while the price falls.

## The advice limit

The agent is not a licensed financial advisor and never writes buy, sell or hold
as its own call on Chaehan's money. It reports the evidence, the score and its
group, and whether the facts since a decision Chaehan recorded fit that
decision or cut against it. When he asks for a recommendation, say this once,
in one sentence, and give everything up to the decision. The decision and the
order stay his.

## Inputs, read before any fetch

1. socrates `memory/stocks.md`: the holdings, the watchlist, every dated
   decision with its deadline and the reasons he gave, the tax-year rules, his
   CEO ratings, and what he recorded about where sale proceeds go (with its
   pointer into `memory/finance.md`). A new buy is read against that last rule.
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
Chaehan's positions, broker, decisions, ratings or amounts into this folder,
its script or its tests: they live in socrates `memory/stocks.md` and in the
note.

## Steps

1. **Fetch and score** the holdings and named candidates, with the CEO
   ratings from `stocks.md`, then the screen:

   ```
   Q="python3 $HOME/Software/Prototypes/agentkit/skills/stock-analysis/scripts/quotes.py"
   $Q arm avgo nvd ... intc amd --set AMD:ceo=2 --set NVD:ceo=1 ... --json $TMPDIR/stocks.json
   $Q <the universe in reference.md, minus the names above> --json $TMPDIR/screen.json
   ```

   In Claude Code each call names `allowed_domains`: `fc.yahoo.com`,
   `query1.finance.yahoo.com`. Sixteen names take ~40 s, the universe ~90 s.
2. **Pick 3-5 new names** from the screen: the highest sum of the four
   computed factors (the CEO shows "?" until rated), ties by the lower P/E, at
   least one robotics name. A name he sold this year stays eligible and its row
   says he held it.
3. **Research every name** with web search (standard mode, several per turn),
   each fact with its date and source link: the last quarter against the
   estimate and the guide; dated events inside 3 months (earnings, lockup
   expiry, refinancing, export rules); the cause of a fall of 30% or more
   from the 1-year high, with the day of the largest fall and any lawsuit or
   filing it set off; and evidence for the CEO rating. A fact not read at its
   source is labeled unverified (RULES.md 244). A row marked † reports in
   another currency than it trades in: take its P/E from a second source.
4. **Rate the CEO** of every name without a rating in `stocks.md`: excellent,
   good or weak, with one line of evidence (a record of strategy carried out,
   a target missed, a turnaround still unproven). These are the agent's
   reading until Chaehan confirms them; rerun with `--set TICKER:ceo=N`.
5. **Read each holding against its decision**: the decision he recorded, with
   its date, or "none recorded", and whether the factors since support it. For
   a new name: what it brings that the holdings lack, or the overlap it
   deepens, and its next report date.
6. **Write, check, file** (below).

## The note

Title `YYYY-MM-DD Stock Review`, notebook Finance, source file
`socrates/stocks/YYYY-MM-DD-stock-review.md`. A second run on the same day
rewrites that note; a new day makes a new note and leaves the earlier ones
untouched (RULES.md 31). Sections in this order:

1. **Summary**, these four parts and nothing else:
   - One or two sentences naming the pattern behind the scores: which factors
     separate the high scorers from the low ones.
   - A grid of stock names, each with its forward P/E ("Nvidia 9×", a
     loss-maker "(loss)"). Rows: Attractive 8-10, Mixed 5-7, Sellable 0-4.
     Columns: Your holdings, New names (his candidates and the proposed ones).
     Names run by score, then P/E, in every cell; an empty cell says "none".
   - The decisions due before the nearest deadline, numbered: each decision he
     recorded or left open, the factor values that support it or cut against
     it, and its date. A stock with no decision gets no sentence; a holding in
     Sellable with a loss inside the tax year is one. While a sale is pending,
     where its money goes is one: his plan, his funding rule in
     `memory/finance.md`, the best-scoring new names, and the cheapest
     high scorer by P/E. Every candidate he named is a decision too.
   - One line of the other dated events inside 30 days.

   From the second review on, a stock that changed group shows its earlier
   group in the grid ("Arm, was Attractive"), and the decisions list only
   what is new or whose evidence changed since the previous review.
2. **Stocks**: an H3 title, the formula line directly above the table, the
   table ranked by score and P/E, then the points rules in one paragraph.
   Columns: Stock (new names marked "new"), Score, one column per factor
   holding its value and points ("66/67/69% → 2"; the CEO cell gives its
   evidence and "your rating" where it is his), P/E now (3 months ago) and the
   fall from the 1-year high, "Your plan, or what it adds".
3. **Sources**: one line per stock with its dated links.
4. **Method**: whose criteria each factor is, the three-year window, the
   closing date of the prices, which CEO ratings are his, one sentence that the
   groups rank the evidence and the decision stays his, and a pointer to
   `reference.md`.

Before the draft, read RULES.md's "The principle of parsimony", rule 19 and
rule 127 (line ranges in `rules.index.md`): a Summary sentence that names no
decision moves below, and a score uses only the columns of its table. Wording
follows `agentkit/AGENTS.md` core 1 and 4: spell out P/E, EBITDA, R&D and
every other abbreviation once; dates YYYY-MM-DD; no thousand separators. Run
`python3 $HOME/Software/Prototypes/agentkit/scripts/wording_lint.py` on the file.

Filing: `$P create --notebook Finance --file <source>` (a same-day rewrite:
`$P write "<title>" --file <source> --base <sha>`), with the sandbox lifted for
that one command, then `$P get` to read it back. Update `stocks.md` (holdings,
CEO ratings, the review's date and title under Current state), run
`memory_lint.py` on it, and commit the source file and `stocks.md` in socrates.
