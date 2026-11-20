# DD-02 agentkit tests on every push, run as a test-first delivery

Task DD-02 of the [DeepSeek delegation plan](<deepseek delegation plan.md>): every push to agentkit runs its test suite on GitHub's runners, and the one red test passes again. Written 2026-11-20 by Claude Opus 5.5; DeepSeek V4.1 Flash runs it in opencode under the runbook skill (`skills/runbook/SKILL.md`).

Board: `docs/deepseek delegation plan.md`, task DD-02. Report: `docs/2026-11-20 dd-02 tests on every push report.md`.

State: not started.
Resume: run the *Resume checks* below and continue at the first test whose row in the *Test log* is not `pass`.

## Delivery rules

- Each test below is checked by the command in its Then; a test passes only on that command's output.
- You change only these files: `tests/test_en_to_hanji.py`, `tests/test_note_build.py`, `tests/test_browser.py`, `pyproject.toml`, `.github/workflows/tests.yml` (new), this runbook's *State* line and *Test log*, the DD-02 row of the board (the claim only), and the report. Never `skills/hanji/scripts/en_to_hanji.py` or `skills/evernote/scripts/note_build.py`: the tests follow the converter of 2026-11-16, not the reverse.
- Python on this machine is `mamba run -n socrates python` (Python 3.14.4, pytest 9.0.3). Every local pytest command below sets `NOTE_BUILD_SOCRATES` itself, since the scripts read socrates' location from it and a launcher may set it to another folder.
- Other sessions commit to agentkit at the same time. Stage each file by its name; when `git status --short` shows a file this runbook does not list, leave it alone and unstaged. A run of the whole suite names the committed test files, `$(git ls-files 'tests/*test_*.py')`, so another session's uncommitted test cannot decide your check.
- Commit after each story whose tests pass, with the message `DD-02 S<n>: <what the story changed>`, and push to `main`. Never push to `main` while a local test fails.
- The probe branch of Story 5 is made in its own worktree under `$TMPDIR`, so the checkout of `main`, which other sessions share, never switches branch.

## What exists today (measured 2026-11-20)

| Item | Value |
|---|---|
| Repository | `agilebean/agentkit`, public, default branch `main`, GitHub Actions enabled, no `.github/` folder |
| Suite on this machine | `mamba run -n socrates python -m pytest -q $(git ls-files 'tests/*test_*.py')`: 1 failed, 587 passed |
| The red test | `tests/test_en_to_hanji.py::test_convert_escapes_masks_marks_colours_and_lists_cell_items`, line 148: `assert "==booked== and grey" in md` |
| Why it is red | commit `1ca5c84` of 2026-11-16 changed `convert()` in `skills/hanji/scripts/en_to_hanji.py`. A run with a text colour (an RGB spread above 60) now stays plain text, and the change list counts it: `1 coloured run(s) lost their colour and stay plain: ...`. Grey text is neither coloured nor counted. A background highlight still becomes `==text==`. The test still expects the old mapping of colour to highlight. |
| Suite on a clean machine | a Python 3.14 venv with `pip install -e ".[config,gmail,evernote]" pytest numpy selenium soundfile` and `HOME` set to an empty folder: 14 failed, 504 passed, 13 skipped |
| The 14 failures | the tests of `tests/test_note_build.py` listed below. Each reaches `enml_module()` in `note_build.py`, which imports socrates' private converter `projects.evernote.src.enml`, and fails with `ModuleNotFoundError: No module named 'projects'`. |
| Skips that already work | without socrates: 6 tests of `test_en_to_hanji.py` (its `needs_socrates` marker), 6 of `test_wording_eval.py`, 1 of `test_say.py`; without Hanji.app: the Hanji tests |
| Without the extra packages | 4 collection errors (selenium for `test_browser.py` and `test_driver.py`, thrift for `test_evernote.py`, numpy and soundfile for `test_speech.py`) and 15 failures (PyYAML for 5 tests of `test_core_config.py`, the Google client for 10 of `test_gmail.py`) |
| Tests that open a local port | measured by wrapping `socket.bind` through a full run: `tests/test_note_build.py::test_the_bridge_uploads_a_photo_with_a_resumable_start_and_one_put` (an `HTTPServer` on 127.0.0.1) and `tests/test_browser.py::TestChromeDriverAttach::test_attaches_with_resolved_driver` (binds 127.0.0.1 and ::1). Every other test only names an address in a string. |
| Runner | `macos-latest`: agentkit holds macOS code (`tests/apple`, `say`, the MLX speech package) and runs on a Mac; macOS minutes are free for a public repository |

The 14 tests of `tests/test_note_build.py` that need socrates:

```
test_a_write_replaces_the_whole_body_and_a_created_note_keeps_its_guid
test_a_write_is_refused_for_a_wrong_link_title_or_an_unstamped_draft
test_a_top_image_stays_and_a_note_edited_since_the_read_is_refused
test_an_image_at_the_foot_stays_like_one_at_the_top
test_a_text_written_elsewhere_is_gated_stamped_and_written_with_its_photos
test_a_photo_below_the_text_is_refused_and_an_edit_of_the_draft_reruns_the_gate
test_the_bridge_uploads_a_photo_with_a_resumable_start_and_one_put
test_a_second_write_does_not_put_in_again_a_photo_the_note_holds
test_photos_the_write_put_at_the_top_in_divs_stay_at_the_top_on_the_next_write
test_a_text_written_elsewhere_goes_to_hanji_with_a_photo_whose_path_has_a_space
test_init_as_is_with_his_words_passes_and_its_read_back_verifies
test_a_rewrite_by_guid_needs_the_text_it_started_from_and_refuses_an_edit_since
test_a_section_write_replaces_one_section_and_keeps_his_edits_and_photos_around_it
test_a_section_edited_since_or_holding_an_image_is_refused
```

## Story 1: the red test follows the converter of 2026-11-16

- [ ] T1.1 Given the red test, when its name and its last four assertions are replaced as below, then `NOTE_BUILD_SOCRATES=$HOME/Software/Prototypes/socrates mamba run -n socrates python -m pytest -q tests/test_en_to_hanji.py` prints no `failed` and no `skipped`, and `git diff --quiet skills/hanji/scripts/en_to_hanji.py` exits 0.

  The name becomes `test_convert_escapes_masks_drops_colours_and_lists_cell_items`. The `enml` string, the call to `eh.convert` and the first two assertions stay. The four lines from `assert "==booked== and grey" in md` to the end of the function become:

  ```python
      assert "booked and grey" in md and "==" not in md
      assert "| Profile<br>• 밝고 따뜻하며<br>• 미국 유학 | x |" in md
      assert any(c.startswith("1 coloured run(s) lost their colour") for c in changes)
      assert not any("highlighted run" in c for c in changes) and any("header" in c for c in changes)
  ```

- [ ] T1.2 Given T1.1, when the whole suite runs with socrates, then `NOTE_BUILD_SOCRATES=$HOME/Software/Prototypes/socrates mamba run -n socrates python -m pytest -q $(git ls-files 'tests/*test_*.py')` prints no `failed`.

## Story 2: tests that need socrates skip without it

- [ ] T2.1 Given `tests/test_note_build.py`, when this marker is defined right after the line `_spec.loader.exec_module(nb)` and put as `@needs_socrates` on each of the 14 tests listed above, then `NOTE_BUILD_SOCRATES=$(mktemp -d) mamba run -n socrates python -m pytest -q -rs tests/test_note_build.py` prints no `failed` and 14 lines that end in `socrates's ENML converter is not checked out`.

  ```python
  needs_socrates = pytest.mark.skipif(not (nb.SOCRATES / "projects/evernote/src/enml.py").is_file(),
                                      reason="socrates's ENML converter is not checked out")
  ```

- [ ] T2.2 Given T2.1, when the same file runs with socrates, then `NOTE_BUILD_SOCRATES=$HOME/Software/Prototypes/socrates mamba run -n socrates python -m pytest -q tests/test_note_build.py` prints no `failed` and no `skipped`.

## Story 3: tests that open a local port carry a marker

- [ ] T3.1 Given `[tool.pytest.ini_options]` in `pyproject.toml`, when it gains the line below under `pythonpath = ["src"]` and the two tests of the row *Tests that open a local port* get `@pytest.mark.local_port`, then `NOTE_BUILD_SOCRATES=$HOME/Software/Prototypes/socrates mamba run -n socrates python -m pytest -q --strict-markers -m local_port --collect-only` lists exactly those two tests, and `NOTE_BUILD_SOCRATES=$HOME/Software/Prototypes/socrates mamba run -n socrates python -m pytest -q --strict-markers $(git ls-files 'tests/*test_*.py')` prints no `failed`. `tests/test_browser.py` imports pytest only inside one test, so it also gains `import pytest` at module level, after the line `from unittest.mock import MagicMock, patch`; the bridge test keeps its `@needs_socrates` above the new marker.

  ```toml
  markers = ["local_port: the test opens a socket on 127.0.0.1; deselect it with -m 'not local_port' where a sandbox refuses the bind"]
  ```

## Story 4: the workflow file, proved on a clean machine first

- [ ] T4.1 Given no `.github/` folder, when `.github/workflows/tests.yml` is written with exactly this content, then `mamba run -n socrates python -c "import yaml; yaml.safe_load(open('.github/workflows/tests.yml'))"` exits 0.

  ```yaml
  name: tests

  on:
    push:
    pull_request:

  jobs:
    pytest:
      runs-on: macos-latest
      timeout-minutes: 15
      steps:
        - uses: actions/checkout@v4
        - uses: actions/setup-python@v5
          with:
            python-version: "3.14"
        - name: Install
          run: python -m pip install -e ".[config,gmail,evernote]" pytest numpy selenium soundfile
        - name: Test
          run: python -m pytest -q -rs --strict-markers
  ```

- [ ] T4.2 Given a fresh venv made the way the runner makes its own, when the suite runs with an empty home and no socrates, then the last line of the commands below shows no `failed`, and every `SKIPPED` line names private data, socrates or Hanji.app. On 2026-11-20 a scratch copy with Stories 1 to 3 printed `553 passed, 27 skipped`.

  ```bash
  V=$(mktemp -d)/venv && H=$(mktemp -d)
  ~/Software/miniforge3/envs/socrates/bin/python -m venv "$V"
  "$V/bin/python" -m pip install -q -e ".[config,gmail,evernote]" pytest numpy selenium soundfile
  env -u NOTE_BUILD_SOCRATES HOME="$H" "$V/bin/python" -m pytest -q -rs --strict-markers -p no:cacheprovider
  ```

## Story 5: GitHub runs it, green on main and red on a broken commit

- [ ] T5.1 Given Stories 1 to 4 committed and pushed to `main`, when the workflow run for the last commit finishes, then `gh run list --workflow tests.yml --branch main --limit 1 --json conclusion,headSha,databaseId` shows `"conclusion":"success"` and a `headSha` equal to `git rev-parse HEAD`. Wait with `gh run watch <databaseId> --exit-status`; a run longer than 15 min fails this test.
- [ ] T5.2 Given `main` green, when a branch holding one failing test is pushed from its own worktree, then its run concludes `failure` and `gh run view <databaseId> --log-failed` names `test_red_probe`.

  ```bash
  W=$(mktemp -d)/probe
  git worktree add "$W" -b dd-02-red-probe main
  printf 'def test_red_probe():\n    assert 1 == 2, "DD-02 red probe"\n' > "$W/tests/test_red_probe.py"
  git -C "$W" add tests/test_red_probe.py
  git -C "$W" commit -m "DD-02 red probe: a failing test that the workflow must catch"
  git -C "$W" push -u origin dd-02-red-probe
  gh run list --workflow tests.yml --branch dd-02-red-probe --limit 1 --json conclusion,databaseId
  ```

- [ ] T5.3 Given T5.2, when the probe is removed with the commands below, then `git ls-remote origin dd-02-red-probe` prints nothing, `git branch --list dd-02-red-probe` prints nothing, and `git log origin/main --oneline | grep -c "red probe"` prints `0`.

  ```bash
  git push origin --delete dd-02-red-probe
  git worktree remove --force "$W"
  git branch -D dd-02-red-probe
  git fetch origin
  ```

## Story 6: the report

- [ ] T6.1 Given Stories 1 to 5, when the report is written to `docs/2026-11-20 dd-02 tests on every push report.md` in the form of the runbook skill, then `python3 scripts/report_check.py "docs/2026-11-20 dd-02 tests on every push report.md"` prints `report_check: PASS`. The table of changes has a row for the red test, the 14 skips, the port marker, the workflow run on `main` with its `databaseId`, and the probe run with its `databaseId`.

## When to stop

- A test whose check fails twice in a row without fewer failures: write the report `stopped at <id>: <the last check's output line>`.
- A step that would change a file outside the list of the delivery rules, delete or weaken an assertion this runbook does not name, or skip a test that needs neither socrates, Hanji.app nor private data.
- A workflow failure on `main` in T5.1 that the clean venv of T4.2 did not show: stop, since the runner differs from the venv, and the frontier session decides.
- Any question for Chaehan: write it as a row of open items in the report, and end the run.

## Resume checks

| Check | Reads | Means |
|---|---|---|
| `git log --oneline -15 --grep "DD-02"` | commits `DD-02 S1` to `DD-02 S4` | the stories with a commit are done |
| `ls .github/workflows/tests.yml` | the file exists | T4.1 done |
| `gh run list --workflow tests.yml --limit 5` | a success on `main` / a failure on `dd-02-red-probe` | T5.1 / T5.2 done |
| `git ls-remote origin dd-02-red-probe` | empty after T5.2 passed | T5.3 done |
| `ls "docs/2026-11-20 dd-02 tests on every push report.md"` | the file exists | Story 6 begun |

## Test log

| ID | Date | Result | Evidence |
|---|---|---|---|
