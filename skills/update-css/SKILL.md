---
name: update-css
description: Update the swim CSS benchmark from a new 200 m + 400 m test, where a 250 m trial is scaled to the 200 m inside itself and a trial with a stop is taken at the effective time the user gives: compute CSS, generate the 60-90% effort zones, record them in config/benchmark.yaml, update the swim tests, and add a row to the Evernote "Swim Benchmarks" note. Use when the user says "update css", "new css test", or reports 400 m and 200 m test times.
---

# Update CSS benchmark (swim)

The user swims a CSS test (all-out 200 m and 400 m), reports both times, and
the benchmark zones (60/70/80/90%) are regenerated from the test. One test,
one update. Never derive the zones from a hypothetical "true CSS" the user
floats in conversation; the measured test is the only anchor unless the user
explicitly says otherwise. Always the latest test: if a newer measured test
exists than the one in `css_history`, process it instead; older entries stay
as history.

## 1. Compute CSS and zones

CSS pace per 100 m in seconds: `(T400 - T200) / 2`. Round the result UP to a
whole second.

Example: 400 m 8:04 (484 s), 200 m 4:02 (242 s) gives (484-242)/2 = 121 s,
not rounded up because it divides exactly.

Two variations in the swim itself, each kept the way the user states it:

- A stop inside a trial (goggles, lane traffic) comes out of the recorded
  wall: a 400 m recorded at 8:10 less a 6 s goggles stop is his 8:04. Use the
  effective time he gives, do not re-derive it from the laps.
- A trial swum at another distance is scaled **inside itself**, never off the
  400 m and never off all the distances: a 250 m in 5:03 (303 s) holds the
  200 m at 303 x 4/5 = 242 s (4:02). Record that value in `test_200m_sec` and
  say in the comment that it came from the 250 m trial.

Zone rule (set by the user; uniform 8 s steps since 2026-09-30), applied to
the rounded CSS:

| Zone | Rule | Example (CSS 2:01) |
|------|------|--------------------|
| 60%  | CSS + 8 s   | 2:09 (aerobic) |
| 70%  | CSS         | 2:01 |
| 80%  | CSS - 8 s   | 1:53 |
| 90%  | CSS - 16 s  | 1:45 |

The 60% row is open at the slow end: every pace at or slower than its target
is also 60% (otherwise slow paces would have no category). All stored values
are whole seconds. No fractional paces.

## 2. Update config/benchmark.yaml (swim repo)

Working directory: `/Users/chaehan/Software/Prototypes/swim` (or open the
repo wherever it lives).

- `analysis.pace_benchmarks_sec_per_100m`: replace all four zone seconds.
- `analysis.css_history`: append the new test at the END (chronological
  order). Entry fields: `date` (quoted YYYY-MM-DD), `css_time_sec` (rounded
  up), `test_200m_sec`, `test_400m_sec`.
- Update the comments so they state the source test date and the zone rule.

## 3. Update the tests

`tests/test_proposal_benchmarks.py` holds the table twice: as `DOCUMENTED`
and in the fixture YAML of
`test_documented_benchmark_table_is_loaded_from_yaml`. Keep both in sync, then
recompute the classification expectations for the new seconds. Classification
is by threshold, so each probe is read against the target it must clear:

- `test_classify_threshold_benchmark`: one probe per zone, at or faster than
  its own target and slower than the next faster one.
- `test_classify_slower_than_target_falls_to_slower_effort`: a pace a few
  seconds slower than the 70% target lands in 60%.
- `test_classify_at_target_is_that_effort`: each target classifies as itself.
- `test_classify_slower_than_band_falls_to_60_with_delta` and
  `test_classify_out_of_band_pace_reports_delta`: the deltas are `|pace -
  target|` against the new 60% and 90% seconds.
- Update the module docstring's description of the table.

`tests/test_css_test_auto_classification.py` reads the real
`config/benchmark.yaml`, so the zone labels it asserts are recomputed against
the new table as well.

Two more copies of the numbers live outside the test file: the worked example
in `README.md` (`A 400 m at 2:02 is 60% because it is slower than the 70%
target (2:01)`) and the `pace_benchmarks_sec_per_100m` comment in
`config/benchmark.yaml`. Sweep both.

The snapshot baselines in `tests/baselines/` carry the generated dashboard.
The table reaches the dashboard only through the zone labels on live reps, so
rebuild the payload once and compare: the 2026-10-16 update moved no label,
but a rep within a second of a target can move. Refresh the baselines only
when one actually did.

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
CSS 2:01 (400m 8:04, 200m 4:02).
- 60% 2:09 (CSS +8)
- 70% 2:01 (CSS)
- 80% 1:53 (CSS -8)
- 90% 1:45 (CSS -16)
```

When the trials were not the standard 200 m and 400 m, one short second
sentence in the same cell says how the numbers were arrived at: the
2026-10-16 row names the 6 s goggles stop taken out of an 8:10 and the 250 m
trial the 200 m was scaled from.

Bullets must be real `<ul><li>` elements in the ENML. The `add-row` command
splits cells on commas, so with commas in the text use the raw read-modify-
write path instead:

1. `get-by-title --raw "Swim Benchmarks"` and take the JSON `content`.
2. Build the new `<tr>` with the same `<td>` styles as the existing rows.
3. Insert it immediately after the first `<tbody>` occurrence.
4. `update-by-title --raw --file <path> "Swim Benchmarks"`, the full ENML
   written to `<path>` first (`--file` keeps the ENML out of argv).

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

- Full pytest suite green, ruff clean on touched files. Snapshot failures
  under `tests/baselines/` that name a date other than this test's are a
  different work item (an uncommitted ingest), not this one.
- Evernote row present at the top of "My Benchmark Times" with the rounded
  zones, verified from the raw ENML.