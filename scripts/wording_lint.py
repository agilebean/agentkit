#!/usr/bin/env python3
"""Check text for the robot markers of RULES.md rule 2, and for a reply written
in the wrong script.

Usage:
  python3 scripts/wording_lint.py [--strict] [--markers PATH ...] FILE [FILE ...]

Reads the shared marker list (`robot_markers.tsv`, at this repo's root) and
reports each hit as `<file>:<line>: <level> '<matched words>' - <fix>`. A
`flag` hit fails the run with exit 2; a `warn` hit is reported only.

`--markers` may be given more than once; the lists are read together, and the
shared list is read only when no `--markers` is given, so a skill that adds its
own list names the shared one as well. `--strict` makes every warn a failure:
a text Chaehan reads as a finished note carries no
contrast frame and no container word at all. The list
is the checkable subset by design: three-item runs, embedded clauses, headings
over one sentence and colon-field blocks stay a writer's pass. `rhythm_hits`
adds what a word list cannot see: three sentences in a row opening with "You",
a paragraph of only instructions, a colon frame ("So the shape is:"), a bold
lead-in and a thousand separator. `scripts/reply_gate.py` runs all of it on
every chat reply as a Claude Code Stop hook.

The language check is mechanical because the drift is not: a Han character in
the writer's own text is a `flag` (RULES.md rule 217). Chaehan reads English,
German and Korean; Chinese in a reply is unreadable to him, and twice in one
session it went out unchecked. Hangul is left alone - a Korean reply is a
legitimate thread language. Inline code and a declared excerpt are skipped, so
a quoted filename or a source's own characters do not trip it.

Every project runs this same list. A project pipeline may wrap the checker for
its own files (socrates: `projects/kubs_dt/pipeline.py lint --session N`).

A quoted excerpt is the source's own text, kept verbatim, and the checker
leaves it alone: its lines sit between `<!-- verbatim -->` and
`<!-- end verbatim -->`. Another author's punctuation, word choices and
sentence shapes are not the writer's to repair, and flagging them trains the
reader to ignore the list. The two marker lines are comments, so a renderer
that shows raw HTML as text would print them; the path that renders an
artifact drops them first (socrates: `script_html` in
`projects/kubs_dt/pipeline.py`, held by its printout test).
"""
from __future__ import annotations

import argparse
import os
import re
import sys

DEFAULT_MARKERS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "robot_markers.tsv")

# A declared quoted excerpt: the lines between these two markers are another
# author's text, and the checker does not read them.
EXCERPT_OPEN = re.compile(r"^\s*<!--\s*verbatim\s*-->\s*$")
EXCERPT_CLOSE = re.compile(r"^\s*<!--\s*end verbatim\s*-->\s*$")

# Han characters: the script of a reply that is not being written in English,
# German or Korean. Kana and Hangul are outside these ranges.
HAN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")


def script_hits(text: str) -> list[tuple[int, str, str]]:
    """Han characters in the writer's own words: (line, the character, the line).

    Inline code is stripped and a declared excerpt is skipped, so a quoted
    filename or another author's characters stay out of the check.
    """
    hits = []
    in_excerpt = False
    for lineno, line in enumerate(text.splitlines(), 1):
        if EXCERPT_OPEN.match(line):
            in_excerpt = True
            continue
        if EXCERPT_CLOSE.match(line):
            in_excerpt = False
            continue
        if in_excerpt:
            continue
        clean = re.sub(r"`[^`]*`", "", line)
        m = HAN.search(clean)
        if m:
            hits.append((lineno, m.group(0), clean.strip()[:90]))
    return hits


# A title (an Evernote note's title, a file's name) names its subject by a
# category noun: "nutritional intake", never "what she gets". A person or a
# sexual act in a title shows in every list, search result and screen share
# (RULES.md rule 20). A weak model cannot judge "embarrassing", so the test is
# lexical: no pronoun for a person, no explicit word.
TITLE_BAD = re.compile(
    r"\b(she|he|her|his|him|hers|they|them|their|gets|gives|swallow\w*|oral|sex|sexual|"
    r"blowjob|cum\w*|orgasm\w*|ejaculat\w*|penis|vagina\w*|naked|nude)\b", re.I)


def title_hits(title: str) -> list[str]:
    """The words that make a title unfit to show anyone (RULES.md rule 20)."""
    return [m.group(0) for m in TITLE_BAD.finditer(title)]


# A name keeps only the words that tell it from its siblings, and an article
# never does (RULES.md rule 70). "the" in any case; lowercase "a" and "an" only,
# so a label such as "Option A" passes.
TITLE_ARTICLE = re.compile(r"(?:^|[\s_-])((?i:the)|a|an)(?=[\s_-]|$)")


def title_articles(title: str) -> list[str]:
    """The articles in a title or file name (RULES.md rule 70)."""
    return [m.group(1) for m in TITLE_ARTICLE.finditer(title)]


def load_robot_markers(path: str = DEFAULT_MARKERS) -> list[tuple[str, re.Pattern, str, re.Pattern | None]]:
    rules = []
    with open(path, encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, 1):
            line = raw.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            cells = line.split("\t")
            if len(cells) < 3 or cells[0] not in ("flag", "warn"):
                sys.exit(f"{path}:{lineno}: a rule reads 'flag|warn <TAB> pattern <TAB> fix [<TAB> exception]'")
            rules.append((cells[0], re.compile(cells[1], re.I), cells[2],
                          re.compile(cells[3], re.I) if len(cells) > 3 and cells[3] else None))
    return rules


def lint_text(text: str, rules) -> list[tuple[int, str, str, str]]:
    """The robot markers in a text: (line, level, the matched words, the fix).

    One hit per line and span: a phrase caught by two rules is reported once.
    Inline code (`pipeline.py`) is stripped before matching: a command's own
    name is not prose. A declared quoted excerpt is skipped whole - the
    checker reads the writer's words, not the source's.
    """
    hits = []
    seen = set()
    in_excerpt = False
    for lineno, line in enumerate(text.splitlines(), 1):
        if EXCERPT_OPEN.match(line):
            in_excerpt = True
            continue
        if EXCERPT_CLOSE.match(line):
            in_excerpt = False
            continue
        if in_excerpt:
            continue
        clean = re.sub(r"`[^`]*`", "", line)
        for level, pattern, fix, except_ in rules:
            m = pattern.search(clean)
            if not m or (except_ and except_.search(clean)):
                continue
            key = (lineno, m.start(), m.end())
            if key in seen:
                continue
            seen.add(key)
            hits.append((lineno, level, m.group(0), fix))
    return hits


# Run-level checks: the forms a word list cannot see, because they live in a run
# of sentences or in a sentence's shape. Chaehan, 2026-11-14: "the constant
# second person wording sounds repetitive and unnatural" and "only instructions
# is also very unnatural". The colon frames and bold lead-ins are what the
# 2026-11-27 chat reply baseline found in replies the marker list passed with
# 0 hits ("So the shape is:", "One number decides it:").
FENCE = re.compile(r"^\s*(?:```|~~~)")
LIST_MARK = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
BOLD_LEAD = re.compile(r"^\s*(?:(?:[-*+]|\d+[.)])\s+)?\*\*[^*\n]+\*\*[:.]?\s*\S")
THOUSANDS = re.compile(r"(?<![\d,.])\d{1,3}(?:,\d{3})+(?![\d,])")
SENTENCE = re.compile(r"\S.*?(?:[.!?](?=\s|$)|$)", re.S)
YOU_OPEN = re.compile(r"^[\"'(]*(?:you|your|yours|you're|you'll|you've|you'd)\b", re.I)
IMPERATIVE = frozenset("""add always apply ask avoid book bring buy call cancel check choose claim
close confirm consider cut do don't drink drop eat email expect file find follow get give go hold
increase keep leave let limit look lower make mention move never note open pay pick plan prefer put
raise read reduce remember repeat reply rest return run save schedule send set show skip sleep start
stop stretch swim take tell text treat try use wait walk watch write""".split())
FRAME_HEAD = re.compile(r"^([A-Z][^:.!?\n]{0,70}?):(?=\s|$)")
FRAME_WH = re.compile(r"^(?:so |and |but |here'?s |here is )?(?:what|why|how|where|when|which|who)\b", re.I)
FRAME_END = frozenset("""is are was were be it this that these here down follows goes means matters
leaves shows says counts decides holds stands remains comes happens verdict answer point shape catch
upshot takeaway gist question rule test reason result call plan line version picture twist trick
kicker key problem issue""".split())

YOU_RUN_FIX = ("three sentences in a row open with 'You': make one a plain statement of fact "
               "(Chaehan, 2026-11-14: \"the constant second person wording sounds repetitive\")")
YOU_SHARE_FIX = "most sentences open with 'You': mix in plain statements of fact, as speech does (core 1)"
IMPERATIVE_FIX = ("a paragraph of only instructions: state the facts they rest on, as speech mixes "
                  "them (Chaehan, 2026-11-14: \"only instructions is also very unnatural\")")
FRAME_FIX = "colon frame: the words before the colon announce the content; write the content as the sentence"
BOLD_FIX = "bold lead-in: write the point as the paragraph's first sentence (RULES.md 19)"
THOUSANDS_FIX = "a thousand separator: write numbers without one (core 8)"


def _prose_blocks(text: str) -> list[list[tuple[int, str]]]:
    """The writer's prose as paragraphs of (line, text): code fences, quotes,
    tables, headings and declared excerpts left out, inline code stripped."""
    blocks, block = [], []
    in_fence = in_excerpt = False
    for lineno, line in enumerate(text.splitlines(), 1):
        if FENCE.match(line):
            in_fence = not in_fence
            line = ""
        elif EXCERPT_OPEN.match(line):
            in_excerpt = True
        elif EXCERPT_CLOSE.match(line):
            in_excerpt = False
            line = ""
        stripped = line.strip()
        if in_fence or in_excerpt or not stripped or stripped[0] in ">|#" or stripped.startswith("<!--"):
            if block:
                blocks.append(block)
                block = []
            continue
        block.append((lineno, re.sub(r"`[^`]*`", "", line)))
    if block:
        blocks.append(block)
    return blocks


def _sentences(block: list[tuple[int, str]]) -> list[tuple[int, str, bool]]:
    """A paragraph's sentences as (line, text, inside a list); a list item
    always starts a sentence. List markers and bold markers are dropped."""
    out = []
    pending: list[tuple[int, str, bool]] = []
    for lineno, line in block:
        is_item = bool(LIST_MARK.match(line))
        body = LIST_MARK.sub("", line).replace("**", "").strip()
        if is_item or not pending:
            pending.append((lineno, body, is_item))
        else:
            ln, prev, item = pending[-1]
            pending[-1] = (ln, prev + " " + body, item)
    for lineno, body, item in pending:
        for m in SENTENCE.finditer(body):
            out.append((lineno, m.group(0).strip(), item))
    return out


def _is_frame(sentence: str) -> bool:
    m = FRAME_HEAD.match(sentence)
    if not m:
        return False
    words = m.group(1).split()
    if len(words) < 2 or len(words) > 8:
        return False
    return bool(FRAME_WH.match(m.group(1))) or words[-1].lower().strip(",") in FRAME_END


def rhythm_hits(text: str) -> list[tuple[int, str, str, str]]:
    """The run-level and shape markers in a text: (line, level, the words, the fix)."""
    hits = []
    total = you = 0
    first_line = None
    for block in _prose_blocks(text):
        for lineno, line in block:
            if BOLD_LEAD.match(line):
                hits.append((lineno, "flag", line.strip()[:50], BOLD_FIX))
            for m in THOUSANDS.finditer(line):
                hits.append((lineno, "flag", m.group(0), THOUSANDS_FIX))
        sentences = _sentences(block)
        run: list[tuple[int, str]] = []
        for lineno, s, _item in sentences + [(0, "", False)]:
            if s and YOU_OPEN.match(s):
                run.append((lineno, s))
                continue
            if len(run) >= 3:
                hits.append((run[0][0], "flag", " / ".join(x[1][:25] for x in run[:3]), YOU_RUN_FIX))
            run = []
        for lineno, s, _item in sentences:
            if _is_frame(s):
                hits.append((lineno, "flag", s.split(":", 1)[0] + ":", FRAME_FIX))
            total += 1
            you += bool(YOU_OPEN.match(s))
            first_line = first_line or lineno
        prose = [s for _l, s, item in sentences if not item]
        if len(prose) >= 3 and len(prose) == len(sentences) and all(
                s.split()[0].lower().strip("\"'(,") in IMPERATIVE for s in prose):
            hits.append((sentences[0][0], "warn", prose[0][:40], IMPERATIVE_FIX))
    if total >= 6 and you / total > 0.6:
        hits.append((first_line or 1, "warn", f"{you} of {total} sentences open with 'You'", YOU_SHARE_FIX))
    return sorted(hits)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--markers", action="append", default=[],
                    help="a robot marker list to read; repeat for several (default: the shared list)")
    ap.add_argument("--strict", action="store_true", help="a warn hit fails the run as a flag does")
    ap.add_argument("--title", action="append", default=[], help="a note title to check (rule 20); the files' own names are always checked")
    ap.add_argument("files", nargs="+", help="files to check")
    args = ap.parse_args(argv)
    rules = []
    for path in args.markers or [DEFAULT_MARKERS]:
        if not os.path.exists(path):
            sys.exit(f"wording_lint: no marker list at {path}")
        rules += load_robot_markers(path)
    flags = warns = 0
    titles = list(args.title) + [os.path.splitext(os.path.basename(p))[0] for p in args.files]
    for title in titles:
        bad = title_hits(title)
        if bad:
            print(f"  title '{title}': flag {bad} - name the subject by a neutral category noun "
                  f"(\"nutritional intake\", never \"what she gets\"), RULES.md 20")
            flags += 1
        articles = title_articles(title)
        if articles:
            print(f"  title '{title}': warn {articles} - a name keeps only the words that tell it "
                  f"from its siblings, and an article never does, RULES.md 70")
            if args.strict:
                flags += 1
            else:
                warns += 1
    for path in args.files:
        if not os.path.exists(path):
            print(f"  missing: {path}")
            continue
        body = open(path, encoding="utf-8").read()
        for lineno, level, match, fix in lint_text(body, rules) + rhythm_hits(body):
            print(f"  {path}:{lineno}: {level} '{match}' - {fix}")
            if level == "flag" or args.strict:
                flags += 1
            else:
                warns += 1
        for lineno, char, line in script_hits(body):
            print(f"  {path}:{lineno}: flag '{char}' - Han characters in your own text: "
                  f"write it in the thread's language (RULES.md 217) | {line}")
            flags += 1
    print(f"wording_lint: {len(args.files)} file(s), {flags} flag(s), {warns} warn(s)"
          + (" (strict: warns fail)" if args.strict else ""))
    return 2 if flags else 0


if __name__ == "__main__":
    sys.exit(main())
