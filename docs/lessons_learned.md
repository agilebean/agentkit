# Lessons learned — agentkit module extraction

**Read this before touching any consumer repo.**

---

## 1. CRITICAL: Never mix module extraction with CLI refactoring

**The cycle:** `browser_download.py` was BOTH extracted to agentkit AND refactored for `--dry-run`. Every fix to one broke the other.

**Timeline:**
1. CLI refactor (test-run→dry-run, save-commission-pdf→save) — works
2. browser/ extraction → shim replaces `browser_download.py` — **broken: renamed function** `chrome_options_for_debugger`
3. Reverted `browser_download.py` to original — **broken: commission PDF parsing** (format missing)
4. **SHOULD HAVE just fixed parsing here (format 4 in `invoice_pdf.py`). Instead:** re-applied agentkit shim — **broken: download again**
5. Reverted download again, fixed SMTP `None` in `run_month.py` — **broken: `status` unbound**
6. Fixed `status` — ✅

**The mistake at step 4:** User said "fix the parsing error." I interpreted it as "keep trying to make the shim work" instead of the obvious fix: add one regex to `invoice_pdf.py` while the original download code was already working.

**Root cause:** Two tasks sharing the same files (`browser_download.py`, `run_month.py`). Every revert to fix extraction undid CLI progress. Every CLI fix was tested against the original file, not the shim.

**DO THIS:** Finish ONE task completely. Test it. Commit. ONLY THEN start the next task. Never interleave.

**How the user's instructions could have prevented this:** They said "don't change the download method" and "fix the parsing error" repeatedly. I interpreted this as "revert the shim" instead of "fix the extracted code in agentkit so it matches the original exactly, then fix parsing".

---

## 2. WRONG: Not installing agentkit in every project's mamba env

**Symptom:** `ModuleNotFoundError: No module named 'agentkit'` at runtime.

**DO THIS:**
```bash
~/Software/miniforge3/envs/decisionmaker/bin/pip install -e ~/Software/Prototypes/agentkit
~/Software/miniforge3/envs/email-digest/bin/pip install -e ~/Software/Prototypes/agentkit
~/Software/miniforge3/envs/invoice-admin/bin/pip install -e ~/Software/Prototypes/agentkit
~/Software/miniforge3/envs/swim/bin/pip install -e ~/Software/Prototypes/agentkit
~/Software/miniforge3/envs/localai/bin/pip install -e ~/Software/Prototypes/agentkit
```

Also add to each repo's CI workflow:
```yaml
- uses: actions/checkout@v4
  with:
    repository: SoHu-Labs/agentkit
    path: vendor/agentkit
- run: pip install -e vendor/agentkit
```

---

## 3. WRONG: Not running the full test suite before pushing

**DO THIS:**
```bash
cd ~/Software/Prototypes/<project>
~/Software/miniforge3/envs/<env>/bin/python -m pytest tests/ -q
```
Never push with known failures.

---

## 4. WRONG: Fixing CI in a separate commit

**DO THIS:** `git commit --amend --no-edit` and force push.

---

## 5. WRONG: Patching pyproject.toml with git URL dependencies

Hatchling blocks direct URL refs. Use CI checkout step instead.

---

## 6. WRONG: Making litellm a hard dependency for mlx-only consumers

Use lazy imports via `__getattr__` in `__init__.py`.

---

## 7. WRONG: Not adding `py.typed` marker to agentkit

Create empty `src/agentkit/py.typed` and add to pyproject.toml:
```toml
[tool.setuptools.package-data]
agentkit = ["py.typed"]
```

---

## 8. WRONG: Forgetting to push agentkit BEFORE consumer pushes

Push agentkit first, wait, THEN push consumer repo.

---

## 9. WRONG: Renaming functions during extraction

When extracting code to agentkit, keep function names IDENTICAL to the original. The agentkit `_browser.py` renamed `build_chrome_options_for_remote_debugging` → `chrome_options_for_debugger`. The shim had to alias it back. This caused the download to break because the alias wasn't applied everywhere.

**DO THIS:** `diff` the original and extracted file. Every function name, signature, and import must match exactly. Only then write the shim.

---

# Lessons learned — coding LLM plan implementation (2026-07-08)

**Context:** A detailed plan was written for a coding LLM to fix 9 tooling issues across agentkit and socrates. The plan included exact code, test code, and verification commands. The LLM implemented the plan, then fixed remaining gaps in a second round.

---

## 10. WRONG: Regex character classes that silently exclude needed characters

**What happened:** The plan specified `r"(?:TOTAL|AMOUNT)[^$\d]*(\d[\d,]*)"` to match the price after the word TOTAL. The `[^$\d]*` was meant to skip non-numeric characters between "TOTAL" and the number, but it also excluded `$`. So `TOTAL: US$3500` failed to match because `$` blocked the gap pattern. Only `TOTAL: 3500` (no dollar sign) matched.

**Why it was hard to catch:** The test `test_parse_price_picks_total_over_line_item` used input `"TOTAL: US$3500.00"` and asserted `"$3500"`. It PASSED. But it passed via the fallback path (`max(all_dollar_prices)` picks the largest dollar amount), not via the TOTAL detection. The test name claimed to test TOTAL detection but actually tested the fallback. The bug was invisible.

**Root cause:** The regex author thought `[^$\d]` meant "skip anything that's not part of the number." They forgot that `$` appears between the keyword and the number in real documents (`TOTAL: $3500`, `TOTAL: US$3500.00`).

**DO THIS:**
- When writing `[^...]` negated character classes, list every character you are excluding and ask: "Could this character appear in the gap between my anchor and my target?"
- Test regexes with inputs that exercise the specific path, not just the overall output. A test that asserts `"$3500" in result` passes whether the value came from TOTAL detection or from the fallback. To test TOTAL detection specifically, use an input where the fallback would give a DIFFERENT answer: `"Premium: $5000\nTOTAL: $3500"`. If the regex is broken, the fallback picks `$5000` and the test fails.
- Name tests after the code path they exercise, not the overall behavior. `test_parse_price_picks_total_over_line_item` should be `test_total_keyword_overrides_larger_line_item_dollar`.

---

## 11. WRONG: Plan tests that pass for the wrong reason

**What happened:** The plan's test for TOTAL detection passed via the fallback path. The implementer added two extra tests (`test_parse_price_total_over_larger_line_item` with `$5000 > $3500`, and `test_parse_price_total_with_dollar_prefix` with `TOTAL: $3500`) that would have failed if the regex were still broken. These caught the bug during implementation.

**Root cause:** When a function has multiple code paths (if/elif/else), a test that only checks the final output cannot distinguish which path was taken. The test passes as long as ANY path produces the expected output.

**DO THIS:**
- For each code path, write a test input where the other paths would produce a different output. If path A gives `$3500` and path B also gives `$3500` for the same input, you are not testing path A.
- Before writing a test, ask: "If I delete the code path I'm testing, would this test still pass?" If yes, the test is useless for that path.

---

## 12. WRONG: Using bare command names in subprocess calls

**What happened:** The plan called `subprocess.run(["markitdown", ...])` with a bare command name. `markitdown` is installed at `~/.local/bin/markitdown`. If the execution environment does not include `~/.local/bin` in PATH, the subprocess fails with `FileNotFoundError`. All tests mocked `subprocess.run` so they never caught this.

**Root cause:** The plan author assumed the test environment and the runtime environment have the same PATH. They do not. Tests mock the subprocess, so PATH resolution never happens during testing.

**DO THIS:**
- Use `shutil.which("markitdown")` to resolve the full path before calling subprocess. If it returns `None`, fail with a clear error: "markitdown not found on PATH."
- Add a test that mocks `shutil.which` to return `None` and asserts the error message and exit code. This test does not mock `subprocess.run`, so it tests the PATH resolution path.

---

## 13. WRONG: Inconsistent method naming between Facade and Backend

**What happened:** The plan added `GmailFacade.download_attachment()` wrapping `backend.download_attachment()`. But the existing pattern is `GmailFacade.get_message()` wrapping `backend.fetch_message_body()` — the Facade renames the method. `GmailFacade.download_attachment()` broke the convention by keeping the same name.

**Root cause:** The plan was written incrementally and did not check the existing Facade naming pattern before adding new methods.

**DO THIS:** Before adding methods to a class, read the existing methods and follow their naming convention. If the Facade renames `fetch_*` to `get_*`, then `download_attachment` on the backend should be `get_attachment` on the Facade. The implementer caught this and renamed it.

---

## 14. WRONG: Leaving gaps unfixed after "done"

**What happened:** After implementing all 9 issues, three gaps remained: (1) no filename collision handling in PDF rename, (2) no pytest config in agentkit pyproject.toml, (3) no auth-error test for Gmail CLI. The implementer did not address these in the first round. They were only fixed after an explicit evaluation flagged them.

**Root cause:** The plan did not mention these edge cases. The implementer followed the plan exactly and declared done when all plan-specified tests passed. Edge cases not in the plan were not addressed.

**DO THIS:**
- After implementing all plan items, do a self-review: "What happens when two files produce the same output filename?" "What if the external tool is not on PATH?" "What if credentials are missing?" These are not plan items — they are robustness checks.
- A plan is a minimum, not a maximum. The implementer should add tests for edge cases the plan missed, even if the plan did not list them.
- Collision handling: always add a `_dedup_path` function when renaming files programmatically. Two PDFs with the same date/provider/price should produce `(2).pdf`, not overwrite.

---

## 15. WRONG: Missing pytest config in pyproject.toml

**What happened:** agentkit had no `[tool.pytest.ini_options]` section. Test discovery relied on `__init__.py` files in each test subdirectory. Most subdirectories did not have `__init__.py`. This worked by luck — pytest's default rootdir discovery found them. But a new test directory without `__init__.py` could be silently skipped.

**Root cause:** The original pyproject.toml was written before test subdirectories existed. No one updated it when test directories were added.

**DO THIS:** Every Python package should have explicit pytest config in pyproject.toml:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```
This makes test discovery deterministic and independent of `__init__.py` files.

---

## 16. WRONG: Generic error handling when specific errors exist

**What happened:** The Gmail CLI caught all exceptions with `except Exception` and returned exit code 1. But `GmailAuthError` is a specific failure that should return exit code 2 (matching the evernote_api convention). A user seeing "Error: No valid Gmail credentials found" with exit code 1 would not know whether it's an auth problem or a network problem.

**Root cause:** The plan did not specify distinct error handling for auth errors. The implementer used a single catch-all.

**DO THIS:**
- Catch specific exceptions before the generic catch-all. `GmailAuthError` before `Exception`.
- Use distinct exit codes: 2 for auth, 1 for generic errors, 0 for success. Match existing conventions in the same codebase.
- Import the specific exception class inside the function, not at module top, to avoid import failures when optional dependencies are not installed.
