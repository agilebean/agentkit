---
name: update-css
description: Update the swim CSS benchmark from a new 200 m + 400 m test: compute CSS, generate the 60-90% effort zones, record them in config/benchmark.yaml, update the swim tests, and add a row to the Evernote "Swim Benchmarks" note. Use when the user says "update css", "new css test", or reports 400 m and 200 m test times.
---

# Update CSS benchmark (swim)

The user swims a CSS test (all-out 200 m and 400 m), reports both times, and
the benchmark zones (60/70/80/90%) are regenerated from the test. One test,
one update. Never derive the zones from a hypothetical "true CSS" the user
floats in conversation; the measured test is the only anchor unless the user
explicitly says otherwise.

## 1. Compute CSS and zones

CSS pace per 100 m in seconds: `(T400 - T200) / 2`. Round the result UP to a
whole second.

Example: 400 m 8:08 (488 s), 200 m 3:45 (225 s) gives (488-225)/2 = 131.5 s,
rounded up to 132 s = 2:12.

Zone rule (set by Chaehan 2026-09-07), applied to the rounded CSS:

| Zone | Rule | Example (CSS 2:12) |
|------|------|--------------------|
| 60%  | CSS + 6 s  | 2:18 |
| 70%  | CSS        | 2:12 (threshold) |
| 80%  | CSS - 6 s  | 2:06 |
| 90%  | CSS - 12 s | 2:00 |

All stored values are whole seconds. No fractional paces.

## 2. Update config/benchmark.yaml (swim repo)

Working directory: `/Users/chaehan/Software/Prototypes/swim` (or open the
repo wherever it lives).

- `analysis.pace_benchmarks_sec_per_100m`: replace all four zone seconds.
- `analysis.css_history`: append the new test at the END (chronological
  order). Entry fields: `date` (quoted YYYY-MM-DD), `css_time_sec` (rounded
  up), `test_200m_sec`, `test_400m_sec`.
- Update the comments so they state the source test date and the zone rule.

## 3. Update tests/test_proposal_benchmarks.py

The table is duplicated in this test file as `DOCUMENTED` and in the fixture
YAML of `test_documented_benchmark_table_is_loaded_from_yaml`. Keep both in
sync, then recompute the classification expectations for the new seconds:

- `test_classify_nearest_benchmark`: pick a probe pace per zone that is
  nearer to its zone than to either neighbor, and assert the label.
- `test_classify_tie_prefers_slower_effort`: the midpoint between the 70%
  and 80% seconds must classify as ("70%", 3).
- `test_classify_out_of_band_pace_reports_delta`: pace 80.0 s classifies as
  "90%" with delta = (90% seconds) - 80.
- Update the module docstring's description of the table.

Run the full suite from the swim repo root and fix failures before moving on:

```
mamba run -n swim python -m pytest -q
mamba run -n swim ruff check src tests
```

## 4. Evernote "Swim Benchmarks"

CLI (from the socrates repo root, never in-process):

```
mamba run -n socrates python -m projects.evernote.src.evernote_api <command>
```

Add a row at the TOP of the first table "My Benchmark Times" (newest first,
above the previous top row). Never append at the bottom.

Row shape: two cells. First cell: the date `YYYY-MM-DD`. Second cell: a short
sentence with the CSS result, then one bullet per zone. Human tone: answer
first, short sentences, no em-dashes, no filler ("Zones from it" and similar
connectives are forbidden; the user removed that phrasing). Numbers exactly as
computed:

```
CSS 2:12 (400m 8:08, 200m 3:45).
- 60% 2:18 (CSS +6)
- 70% 2:12 (CSS, threshold)
- 80% 2:06 (CSS -6)
- 90% 2:00 (CSS -12)
```

Bullets must be real `<ul><li>` elements in the ENML. The `add-row` command
splits cells on commas, so with commas in the text use the raw read-modify-
write path instead:

1. `get-by-title --raw "Swim Benchmarks"` and take the JSON `content`.
2. Build the new `<tr>` with the same `<td>` styles as the existing rows.
3. Insert it immediately after the first `<tbody>` occurrence.
4. `update-by-title --raw "Swim Benchmarks" "<full enml>"`.

Verify by re-reading with `--raw`: the new row must be the first row and
contain `<li>` elements. The `--markdown` export flattens lists to slash-
separated text; that flattening is an export artifact, not a defect.

Lock recovery: if the write exits 4 with "locked", the note is open in an
editing session. Activate Evernote (`osascript -e 'tell application
"Evernote" to activate'`), run `close-note "Swim Benchmarks"`, wait about 45
seconds, retry the write once. If `close-note` reports the window is not on
the current Space, activate Evernote and check the window count via System
Events first (`count of windows` must be 1), then close and retry. Never
retry a locked write more than twice.

## 5. Done

- Full pytest suite green, ruff clean on touched files.
- Evernote row present at the top of "My Benchmark Times" with the rounded
  zones, verified from the raw ENML.