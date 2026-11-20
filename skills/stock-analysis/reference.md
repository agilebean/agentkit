# Stock analysis: reference

The score and its points rules are in `SKILL.md` ("The score"); `scripts/quotes.py`
computes Cash, Tech, Debt and Outlook, and CEO is set by hand with `--set`.

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
