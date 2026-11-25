#!/usr/bin/env python3
"""Refuse a commit whose staged files hold a term of the private replacement list.

    python3 scripts/private_term_check.py [LIST] < staged-paths

agentkit is public, and DD-03 rewrote its history to take personal terms out. The list
(`real==>replacement` lines, `regex:` or `literal:` prefixes as in git filter-repo) is
private and lives in socrates; this check reads it when it exists and skips when it does
not (CI, another machine). It reads each staged blob (`git show :path`), and it reports
the path, the list rule's number and the count, never the term. Exit 1 on any hit.
"""
import os
import re
import subprocess
import sys

DEFAULT = os.path.expanduser(
    "~/Software/Prototypes/socrates/docs/human quality/data/history replacements.txt")


def patterns(path: str) -> list[tuple[int, re.Pattern[str]]]:
    out = []
    with open(path, encoding="utf-8") as f:
        rules = [ln.rstrip("\n") for ln in f if "==>" in ln and not ln.startswith("#")]
    for k, rule in enumerate(rules, 1):
        real = rule.split("==>", 1)[0]
        if real.startswith("regex:"):
            out.append((k, re.compile(real[6:], re.I)))
        else:
            out.append((k, re.compile(re.escape(real.removeprefix("literal:")), re.I)))
    return out


def hits(text: str, pats: list[tuple[int, re.Pattern[str]]]) -> list[tuple[int, int]]:
    return [(k, n) for k, p in pats if (n := len(p.findall(text)))]


def main(argv: list[str]) -> int:
    path = argv[0] if argv else DEFAULT
    if not os.path.exists(path):
        return 0
    pats = patterns(path)
    bad = 0
    for name in (ln.strip() for ln in sys.stdin):
        if not name:
            continue
        blob = subprocess.run(["git", "show", f":{name}"], capture_output=True)
        if blob.returncode:
            continue
        for k, n in hits(blob.stdout.decode("utf-8", "replace"), pats):
            print(f"private_term_check: {name}: {n} hit(s) of list rule {k}; "
                  "replace the term before committing", file=sys.stderr)
            bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
