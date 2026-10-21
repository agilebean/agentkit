---
description: Compare a swim date with the previous two comparable sessions, per effort level
---

Compare the swim date in `$ARGUMENTS` with the two most recent comparable
sessions before it:

```
cd ~/Software/Prototypes/swim && mamba run -n swim python scripts/compare_sessions.py --date $1
```

The script picks the comparison dates itself: the previous sessions that carry
every effort level the target has (cooldown ignored), so a classic set is
compared with classic sets, not with an aerobic 2x400.

Present the table it prints **unchanged**, at the top of the reply:

| Effort | Pace (s/100 m) | DPS (m/stroke) | SR (strokes/min) |
|---|---|---|---|

- Rows are effort levels; each cell chains the dates oldest → newest.
- No rep-count column. Rep distance belongs in the effort label (`60% (100 m)`).
- Stroke metrics are effective-stroke basis: Apple `stroke_count` counts one
  unit per two full strokes (`BENCHMARK_REPORTED_STROKES_TO_EFFECTIVE`), so
  DPS = distance / (reported × 2) and SR = (reported × 2) / rep wall minutes.
  Never quote the raw count as strokes per minute.
- Main-set swim time is the sum of the main-set reps' own wall seconds
  (cooldown excluded). Rest between reps is the watch span minus that swim
  time; they are never the same number and rest is never called swim time.

Then add 3–5 bullets reading the numbers: which metric moved at which effort,
whether a pace change came from stroke length (DPS) or turnover (SR), and what
the finisher / cooldown did relative to the earlier sessions. Quote a delta
with its unit and direction (`DPS −0.13 m/stroke at 60% at an unchanged
cadence`). Do not speculate about causes that the numbers do not show, and do
not propose training changes unless asked.
