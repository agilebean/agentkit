---
description: Report OpenCode wait times (model, tools, question waits, timeouts)
---

Run the latency report and summarize the output:

```
python3 ~/Software/Prototypes/socrates/projects/agent_latency/analysis/latency_report.py --compare $ARGUMENTS
```

Report, in this order:
1. the period comparison and the six PLAN.md success measures (the `ok`/`MISS` block),
2. the totals table,
3. the question-wait distribution,
4. every timeout, failed call, or ≥30 s slow call.

Do not act on the findings unless asked.
