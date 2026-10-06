---
description: Report OpenCode wait times (model, tools, question waits, timeouts)
---

Run the latency report and summarize the output:

```
python3 ~/Software/Prototypes/socrates/projects/agent_latency/analysis/latency_report.py $ARGUMENTS
```

Report the totals table, the question-wait distribution, and every timeout or
≥30 s slow call. Do not act on the findings unless asked.
