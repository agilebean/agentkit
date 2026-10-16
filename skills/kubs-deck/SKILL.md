---
name: kubs-deck
description: Build, fix, or verify a KUBS DT session deck (the E01-E08 Keynote files in the session folders). Covers the preflight that names what must stay, the deck's measured reference values, the deckcheck gate that runs before installing, and the log and memory record. Use when the user reports a defect in a session deck, asks for a change to one, or when any pass is about to install a deck.
---

# KUBS deck passes

Every deck defect that recurred had one shape: a pass re-derived something the deck already fixed - a box, an inset, a construction, a spec's scope - and no check could contradict it. This skill is the ordered pass; the values live in one file and the checks in one command.

The three artifacts this skill runs on:

- `projects/kubs_dt/deck_reference.json` - the deck's measured reference (the values). Read it before creating or replacing any element.
- `projects/kubs_dt/deckcheck.py`, wrapped as `pipeline.py deckcheck --session N` - the differential checks.
- `agentkit/rebuild_defects.md` - the failure classes with their instances and the user's words; read it when a report smells like a repeat.

## Step 0 - the preflight (before any write; its answers go in the report)

1. **What class does the instruction govern?** A spec on one instance, a class-wide spec, a new element, a removal. Enumerate the instances before touching anything. "All pasted slides on white" means every page whose background is not the theme's; "the Annex is optional" means every carrier that lists the reading. State the class and the count in your report, and sweep all of it in this pass (rule 136).
2. **What must stay?** List the artifact's standing requirements: the page backgrounds, the band-title anchor, the overview chart's session marks, the divider boxes, the page numbering. A new instruction constrains these; it replaces one only when it says so. Open a sibling deck (E06 to E08) and see what a valid instance looks like before deciding (rule 135).
3. **Does the element already exist as a finished asset?** Search the record (`memory/kubs.md`), the session's `_assets/`, `KUBS DT Course Design/` (including `chart_v9/`), and the other session decks. A finished asset is used whole; assembling one from another instance's pixels leaves seams - the 2026-10-09 cell ring carried E06's row strokes and overhung the rounded rectangle (rule 134).
4. **Who else is writing these files?** The user runs several sessions over one folder set. Before any write: `openchamber` `session.list` scoped to the directory (a busy sibling), the stage's fresh files, the deck's mtime. A text carrier that moved under you is still yours to edit - re-read the changed lines (RULES.md 141); the deck has one writer - if a sibling pass owns it, park the deck step or hand it to the owner, and the md/script sweep still lands.

## Step 1 - the values (never invent geometry)

Read `deck_reference.json`. The essentials:

| Element | Value |
| --- | --- |
| Band and title | band image (0,12) 1920x112, the IMAGE ALONE - no shape behind it; title box (38,34) 1859x73; the deck's titles share one column within 10 px (E05 measured x 38-40), ink top at y 44 |
| Overview page (slide 2) | one image: the session's `chart_v9/chart_S<n>_v9.png` composited onto a 1920x1080 white sheet, placed at (0,0); the chart itself sits at (121,0) |
| Chart marks | green (62,141,39), inset 2 px, stroke 12 px, radius 34; the session's week row and, inside it, the session's own cell |
| Figure slot | 1662 px wide at x 129 (Fig 2.4 page y 137 h 930; the tip page y 222 h 759) |
| Box format (diagrams, figures) | `figure_box_format`: a standard shape contains its text; every text centred in its box, each box's stack centred vertically; line-broken box-like sizes; per-semantic colours; every box its own group inside its family group |
| Dividers | title box (111,399) Georgia-Bold 108; subtext box (115,576) 1325x184 |

A page whose title was re-created, whose figure was redrawn, or whose chart was swapped is where these values get violated.

**The band is the image alone, and a copied page is not a reference.** A page duplicated from another page brings that page's objects along: the deck family's older banded pages carry a band SHAPE at the same (0,12) 1920x112 rect, whose 2 px red outline (#982B15) is hidden by the band image except for its outer half - a full-width hairline at y 11 and y 124-125 - and which shades the page around the band. It is visible whenever the image sits on the shape, on a blue band as on a red one. Where the band came from a duplicate, build it from this file and delete the shape, and check the page's object dump (a banded page carries the image and the deck's hidden 64 pt title copies, no shape at (0,12) 1920x112). **Identity, not position, decides the removal:** on E01's banded pages the band IS the shape - its blue fill is the band and the red outline is its border - and deleting it would delete the band; those take the opposite fix, the band image laid over the shape with the title re-created above. Measured 2026-10-12: 17 pages carry the hairline. Ten were fixed by deletion that day (E02 3-5, E03 61, E06 5-6, E07 3-4, E08 3-4). Six are E01 4, 5, 6, 7, 11, 20 (band-is-the-shape) and one is E02 6 (the hairline is baked into a pasted full-page render); both closed on 2026-10-13 by a build - the recipes and their measured numbers are `band.build_recipe` and `band.render_patch`, and the two traps they name are that a created text item lands centred in the default style (never at index count-1, where a template placeholder accepts text, font and colour but ignores geometry) and that a created title overflows its box by wrapping, not by shrinking. Four pages carry the object with nothing visible (E01 9-10, E03 62-63). E04 and E05 are clean, E05 since its nine shapes were deleted on 2026-10-09. The `band.construction`, `band.defect_signature` and `band.leftover_shape_instances_2026_10_12` fields carry the values.

## Step 2 - the build

- Work on a build copy in the stage; install with Keynote closed (rule 88). Never write a file Keynote holds open.
- **A string-only change** (text that already exists on slides; no new element, no geometry) rides the ops path, not `/slides`: stage copy, `AS_SLIDES_READ` dump, an ops TSV (`txt <slide> <scope> <k> <value>`), `AS_SLIDES_APPLY`, a before/after export diff (only the touched pages may differ), `deckcheck`, byte-checked install. `/slides` runs only when the md is the deck's live source; with hand edits beyond the md it stays parked. Two traps from the 2026-10-11 pass: the stage copy's name must carry the deck's stem (the export finds the document by name prefix), and the read leaves its copy open - close it before `deckcheck`, whose own open fails on it. The full recipe with its driver pattern is in `memory/kubs.md` (Tooling, the two-string pass bullet).
- A pass that only reads works against Chaehan's open document directly - no `open`, no `close`, no save in the script (a hand-rolled open is the abandoned 2026-10-09 class; a `close` of a document the pass did not open is the 2026-10-03 class), and it proves no-touch by the file's mtime before and after - an md5 proves nothing while he edits. Fills, strokes and builds read nowhere; those come from the exported page's pixels (2026-10-10).
- A slide's page carries its own full 1920x1080 white background; the theme is never relied on, and the exported page is the test (rule 133).
- Keynote facts that bite (from the deck's log): `make new image` must sit inside `tell slide N` (`at slide N` fails -10000); reading `position` inside a `tell slide` block throws a `sipo` coercion error (-1700), so compute the arithmetic in Python, set positions last, and verify from the export; paragraph alignment is not scriptable, so a centred title is aligned by its box; a new image appends last in the enumeration.
- When an element's text or construction comes from a source (a book figure, a paper), the source supplies the content only. Grouping, geometry and construction come from the deck - the slide's own title teaches the structure it wants (rule 134; the tip figure's INTERPRETATIONS header was the counterexample).
- A new element the user will edit or animate later - a diagram, a row of boxes, a table - is built from the slide's own objects (shapes, text items, the deck's own fonts), never rasterised: a render is right only for content that is itself a render (a book figure, a photo). Shape fill, stroke and corner radius are not scriptable (probed 2026-10-10: `background color` fails at runtime), so a created box carries the theme's default look - that styling remainder is the user's hand pass, named in the report, never traded for a flattened image (rule 104; `rebuild_defects.md` class 6). The settled look for this chart family - per-semantic colours, semantic groups with a centre-out build, line-broken boxes, middle-aligned texts, all hand-set - is the `figure_box_format` block in `deck_reference.json` (Step 1): read that block and the live page's construction before writing a box, and measure each text's ink centre against its box centre from the export (within 8 px; each box's content stack within 12 px) - the numbers go in the report (2026-10-12: "you forgot many design elements i specified in that slide of e05, like all middle aligned").

## Step 3 - the gate (before installing)

1. Run `mamba run -n socrates python3 projects/kubs_dt/pipeline.py deckcheck --session N`. It exports the deck and checks: every page fully opaque; the band titles' column (one column per deck, spread <= 10 px; E05 measures x 38-40) with their ink top at y 44; no stroke row outside the band image (the leftover band shape); and the session's chart marks against the session's own chart file. Exit 2 means do not install; report the flagged lines.
2. Look at every changed page, magnified at the changed region - not fitted. A fitted view hid a 6 px overhang while three measurements passed (rule 137).
3. Compare each changed page against the page it copies (the reference instance), not against your intent. "It looks right" is not a check; "its ink sits at the same coordinates as the tip page's" is.
4. An install into an EXISTING deck (slides added to a deck that has its own pages) exports the WHOLE deck before the write and compares every page after it: the added pages against their tiles, the rest against that baseline. Keynote's `save` writes the whole document, and an object outside the range you touched can be re-linked by it and appear changed — 2026-10-16, E08: the seven story slides landed byte-exact while the same save surfaced a stock illustration that covered a screenshot on page 12 (`rebuild_defects.md` class 7). A page you did not touch is not a page the save did not touch.

## Step 4 - install and record

Backup to the stage, quit Keynote, copy the build to the session folder, reopen, and re-export to confirm. Log entry in the session's `_log.md`: the instruction in the user's words, the class, what was swept, the measured result, the backups. Memory only when the state changed: the current-state bullet in `memory/kubs.md`; a new class or value goes to `agentkit/rebuild_defects.md` and `deck_reference.json` first, and memory points there.

## The failure classes this pass exists to stop

| Class | One-line trigger | Enforced by |
| --- | --- | --- |
| Reference geometry re-derived | an element that exists elsewhere in the deck is created or replaced, or inherited from the page a new page was duplicated from | the values file; the band, stroke and chart checks |
| A standing requirement dropped | a new instruction on an artifact with existing requirements | preflight 2; the chart check |
| A spec applied to one instance | "all", "every", or a scope the user can see | preflight 1; the pages check |
| Verification that cannot fail | any correctness claim | deckcheck; magnified reads |
| Source structure as the spec | a figure or page built from a book or earlier deck | preflight 3; rule 134 |
| A live element installed as a flattening | a new element the user must edit or animate (a diagram, boxes, a table) | the build step's form rule; rule 104 |
| An install checked only where it wrote | slides added to an existing deck; the pass compares the added pages alone | Step 3.4 — the whole-deck export before the write, every page compared after it (class 7) |

## Report

State what is now true (the fixed pages, the sweep, the measured exports), then what waits on the user, then the detail - never the process order. Name the class when the report answers a defect that had recurred, and name the check that would have caught it. The complete inventory is `agentkit/rebuild_defects.md`.
