# Lessons learned — agentkit module extraction

**Read this before touching any consumer repo after extracting shared code.**

---

## 1. WRONG: Not installing agentkit in every project's mamba env

**Symptom:** `ModuleNotFoundError: No module named 'agentkit'` at runtime.

**False assumption:** "I ran `pip install -e .` in the agentkit directory, so all projects can import it."

**Reality:** Each project uses its OWN mamba environment. Installing in the base env or another project's env does nothing for the other envs.

**DO THIS:**
```bash
# After every extraction, install agentkit in EVERY consumer env:
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

## 2. WRONG: Not running the full test suite before pushing

**Symptom:** CI failures that were "pre-existing" but actually caught by tests I skipped.

**False assumption:** "I ran `test_smoke.py` and `test_config.py`, so everything else must be fine."

**Reality:** My shim changes (new imports, changed function signatures) can break tests I didn't run. Import errors happen during collection, before any test runs. `-x` stops at the FIRST error — hiding subsequent ones.

**DO THIS:**
```bash
cd ~/Software/Prototypes/<project>
~/Software/miniforge3/envs/<env>/bin/python -m pytest tests/ -q
# Fix ALL failures. If some are pre-existing, fix them anyway —
# they're now part of the migration scope.
```

Never push with known failures. Never skip tests with `--ignore` unless you've verified they were already broken before your change.

---

## 3. WRONG: Fixing CI in a separate commit instead of amending

**Symptom:** `git bisect` lands on a broken commit. History shows "fix" commits that should have never existed alone.

**False assumption:** "I'll fix it in the next commit."

**Reality:** Every commit on `main` must pass CI. A broken commit in the middle breaks `git bisect` for everyone forever.

**DO THIS:**
```bash
# Fix the issue
git add <fixed files>
git commit --amend --no-edit
git push --force-with-lease origin main
```

One commit = one complete, working change. No "fixup" or "chore: re-trigger CI" commits. CI was never meant to see the broken state.

---

## 4. WRONG: Patching `pyproject.toml` with git URL dependencies

**Symptom:** CI fails with `ValueError: Dependency #1 cannot be a direct reference` (hatchling) or `fatal: could not read Username` (private repo auth).

**False assumption:** "I'll add `agentkit @ git+https://...` to dependencies so pip installs it automatically."

**Reality:** 
- Hatchling blocks direct URL refs by default (needs `[tool.hatch.metadata] allow-direct-references = true`)
- Private repos need authentication that CI tokens can't provide cross-repo
- The CI checkout step already handles this — don't duplicate it

**DO THIS:**
- Install agentkit in CI via checkout + `pip install -e vendor/agentkit` (already works)
- Do NOT add agentkit to `pyproject.toml` dependencies
- If you must, use `[tool.hatch.metadata] allow-direct-references = true` AND make agentkit public

---

## 5. WRONG: Assuming `repo_root()` finds the right project

**Symptom:** Tests fail with paths pointing to `agentkit/` instead of the consumer project.

**False assumption:** "`repo_root()` walks up from CWD and always finds the right project."

**Reality:** `repo_root()` walks from CWD first. If your shell is in `~/Software/Prototypes/agentkit`, it finds agentkit, not the consumer project.

**DO THIS:**
- Always run tests from the consumer project's directory: `cd ~/Software/Prototypes/<project> && pytest tests/`
- Consumer wrappers pass `env_var` parameter: `return _repo_root(env_var="INVOICE_ADMIN_REPO_ROOT")`
- CI runs from project root — so this only bites you locally

---

## 6. WRONG: Skipping the walkthrough questions before implementing

**Symptom:** Wrong decisions discovered during code review or CI failure that could have been caught before writing code.

**False assumption:** "The questions are optional, I'll just implement what the plan says."

**Reality:** The walkthrough questions catch API mismatches, default behavior conflicts, and test compatibility BEFORE you write a line. Skipping them → rework.

**DO THIS:**
- Read the walkthrough questions for the module
- Answer them with the user
- ONLY THEN start writing code

---

## 7. WRONG: Making litellm a hard dependency for mlx-only consumers

**Symptom:** `ModuleNotFoundError: No module named 'litellm'` in local-chat which only uses `MlxLlm`.

**False assumption:** "All LLM consumers use litellm."

**Reality:** local-chat uses ONLY the mlx backend. The `llm/__init__.py` eagerly imported litellm, breaking mlx-only consumers.

**DO THIS:**
- Use lazy imports via `__getattr__` in `__init__.py`:
```python
def __getattr__(name: str):
    if name in ("complete", "complete_with_tools", ...):
        from agentkit.llm._litellm import complete, ...
        return globals().get(name) or locals()[name]
    raise AttributeError(...)
```
- Always test with the LEAST capable consumer first (local-chat has no litellm)

---

## 8. WRONG: Not adding `py.typed` marker to agentkit

**Symptom:** mypy errors: `Skipping analyzing "agentkit.core": module is installed, but missing library stubs or py.typed marker`

**Fix:** Create empty `src/agentkit/py.typed` and add to pyproject.toml:
```toml
[tool.setuptools.package-data]
agentkit = ["py.typed"]
```

**DO THIS immediately after Phase 0.** Every project that type-checks will need it.

---

## 9. WRONG: Forgetting to push agentkit BEFORE consumer pushes

**Symptom:** CI fails because agentkit's latest code isn't on `main` yet when consumer CI clones it.

**False assumption:** "I pushed both repos, they're both live."

**Reality:** Push order matters. Consumer CI triggers on the consumer push and clones agentkit `main` at that moment. If agentkit hasn't been pushed yet, CI gets stale code.

**DO THIS:**
1. Push agentkit first
2. WAIT for the push to complete
3. THEN push the consumer repo
