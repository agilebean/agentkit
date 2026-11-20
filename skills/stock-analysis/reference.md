# Stock analysis: rubric and universe

The script `scripts/quotes.py` computes four factors; the agent sets catalysts
and may override a computed factor with a stated reason. Each factor runs 1 to 5,
5 the best. Weights (chosen 2026-11-20, "Risk-first"): financing 35, growth 25,
valuation 20, catalysts 10, trend 10. Score = sum of weight × factor / 5, from
20 to 100.

## Factors

| Factor | 5 | 4 | 3 | 2 | 1 | Moves |
|---|---|---|---|---|---|---|
| Financing | net cash | net debt under 1× EBITDA (earnings before interest, taxes, depreciation and amortization) | 1-2.5× | 2.5-4× | above 4×, or net debt with no EBITDA | negative free cash flow: -1 |
| Growth | revenue up more than 50% a year | 25-50% | 10-25% | 0-10% | falling | next year's earnings estimate up 5% in 90 days: +1; down 5%: -1 |
| Valuation | forward P/E (price over next year's earnings) ÷ growth under 0.8 | 0.8-1.2 | 1.2-1.8 | 1.8-2.5 | above 2.5 | forward P/E down 30% or more in 3 months on an earnings estimate cut by less than 5%: +1; growth counted at most 50%; above 20× sales: at most 2 |
| Valuation, no growth | | forward P/E under 12 | 12-20 | 20-30 | 30 or more | |
| Valuation, loss-maker | | EV (enterprise value) under 3× sales | 3-6× | 6-12× | 12× or more | |
| Trend | above the 200-day average, 3 months up 10% or more | above, 0-10% | above but down, or below but up | below, down less than 20% | below, down 20% or more | listed under 200 days: 3-month return alone, at most 4 |
| Catalysts (hand) | a dated event in 3 months likely to lift estimates (a guide raise, a contract start, an index entry) | a positive event with a date | none dated, or mixed | a dated risk (lockup expiry, refinancing, a rule) | a dated event likely to cut estimates or force a raise of equity | |

Hand overrides the numbers miss: leases and purchase commitments outside reported
debt, capital spending above market value that must still be financed, one
customer above a third of revenue. Lower financing by the evidence, never raise
it above what the balance sheet shows.

## Listings

| Ticker | Analysis | Shown beside it | Why it differs |
|---|---|---|---|
| NVD | NVDA (Nasdaq, USD) | NVD.DE (EUR) | Nvidia's German listing |
| FB2A | META (Nasdaq, USD) | FB2A.DE (EUR) | Meta's German listing |
| SPCX | SPCX (Nasdaq, USD) | none | SpaceX Class A, listed 2026-06-12, not the older SPAC ETF |

## Universe for new names

Screened each run, minus his holdings and named candidates. Add a name when a
run's research finds one that fits; remove one that delists.

| Group | Tickers | Why they are here |
|---|---|---|
| Chips and foundry | TSM, MU, 000660.KS (SK hynix), 005930.KS (Samsung), MRVL, QCOM | make or design the chips and memory AI runs on |
| Chip equipment and design software | ASML, AMAT, LRCX, KLAC, SNPS, CDNS | sell to every chipmaker, whoever wins |
| Networking and data-center power | ANET, ALAB, CRDO, VRT, SMCI | connect, power and cool the AI clusters |
| AI platforms and cloud | MSFT, GOOGL, AMZN, NBIS, PLTR | rent compute or sell AI software |
| Robotics and automation | TSLA, ISRG, SYM, TER, ROK, ABBN.SW (ABB), 6954.T (Fanuc), 6861.T (Keyence), 6506.T (Yaskawa), 277810.KQ (Rainbow Robotics), 454910.KS (Doosan Robotics), 005380.KS (Hyundai Motor, owner of Boston Dynamics), SERV | build robots, their parts or the automation they run in |

Watch: Anthropic (reported ticker ANTP; Yahoo had no listing on 2026-11-20).
