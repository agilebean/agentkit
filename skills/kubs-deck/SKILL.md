---
name: kubs-deck
description: Build, fix, or verify a KUBS DT session deck (the E01-E08 Keynote files in the session folders). Covers the preflight that names what must stay, the deck's measured reference values, the deckcheck gate that runs before installing, and the log and memory record. Use when the user reports a defect in a session deck, asks for a change to one, or when any pass is about to install a deck.
---

# KUBS deck passes

Every deck defect that recurred had one shape: a pass re-derived something the deck already fixed - a box, an inset, a construction, a spec's scope - and no check could contradict it. This skill is the ordered pass; the values live in one file and the checks in one command.

The three artifacts this skill runs on:

- `projects/kubs_dt/deck_reference.json` - the deck's measured reference (the values). Read it before creating or replacing any element.
- `projects/kubs_dt/deckcheck.py`, wrapped as `pipeline.py deckcheck --session N` - the differential checks.
- `agentkit/rebuild_defects.md` - the five failure classes with their instances and the user's words; read it when a report smells like a repeat.

## Step 0 - the preflight (before any write; its answers go in the report)

1. **What class does the instruction govern?** A spec on one instance, a class-wide spec, a new element, a removal. Enumerate the instances before touching anything. "All pasted slides on white" means every page whose background is not the theme's; "the Annex is optional" means every carrier that lists the reading. State the class and the count in your report, and sweep all of it in this pass (rule 136).
2. **What must stay?** List the artifact's standing requirements: the page backgrounds, the band-title anchor, the overview chart's session marks, the divider boxes, the page numbering. A new instruction constrains these; it replaces one only when it says so. Open a sibling deck (E06 to E08) and see what a valid instance looks like before deciding (rule 135).
3. **Does the element already exist as a finished asset?** Search the record (`memory/kubs.md`), the session's `_assets/`, `KUBS DT Course Design/` (including `chart_v9/`), and the other session decks. A finished asset is used whole; assembling one from another instance's pixels leaves seams - the 2026-10-09 cell ring carried E06's row strokes and overhung the rounded rectangle (rule 134).

## Step 1 - the values (never invent geometry)

Read `deck_reference.json`. The essentials:

| Element | Value |
| --- | --- |
| Band and title | band image (0,12) 1920x112; title box (38,34) 1859x73; the deck's titles share one column within 10 px (E05 measured x 38-40), ink top at y 44 |
| Overview page (slide 2) | one image: the session's `chart_v9/chart_S<n>_v9.png` composited onto a 1920x1080 white sheet, placed at (0,0); the chart itself sits at (121,0) |
| Chart marks | green (62,141,39), inset 2 px, stroke 12 px, radius 34; the session's week row and, inside it, the session's own cell |
| Figure slot | 1662 px wide at x 129 (Fig 2.4 page y 137 h 930; the tip page y 222 h 759) |
| Dividers | title box (111,399) Georgia-Bold 108; subtext box (115,576) 1325x184 |

A page whose title was re-created, whose figure was redrawn, or whose chart was swapped is where these values get violated.

## Step 2 - the build

- Work on a build copy in the stage; install with Keynote closed (rule 88). Never write a file Keynote holds open.
- A slide's page carries its own full 1920x1080 white background; the theme is never relied on, and the exported page is the test (rule 133).
- Keynote facts that bite (from the deck's log): `make new image` must sit inside `tell slide N` (`at slide N` fails -10000); reading `position` inside a `tell slide` block throws a `sipo` coercion error (-1700), so compute the arithmetic in Python, set positions last, and verify from the export; paragraph alignment is not scriptable, so a centred title is aligned by its box; a new image appends last in the enumeration.
- When an element's text or construction comes from a source (a book figure, a paper), the source supplies the content only. Grouping, geometry and construction come from the deck - the slide's own title teaches the structure it wants (rule 134; the tip figure's INTERPRETATIONS header was the counterexample).

## Step 3 - the gate (before installing)

1. Run `mamba run -n socrates python3 projects/kubs_dt/pipeline.py deckcheck --session N`. It exports the deck and checks: every page fully opaque; the band titles' column (one column per deck, spread <= 10 px; E05 measures x 38-40) with their ink top at y 44; and the session's chart marks against the session's own chart file. Exit 2 means do not install; report the flagged lines.
2. Look at every changed page, magnified at the changed region - not fitted. A fitted view hid a 6 px overhang while three measurements passed (rule 137).
3. Compare each changed page against the page it copies (the reference instance), not against your intent. "It looks right" is not a check; "its ink sits at the same coordinates as the tip page's" is.

## Step 4 - install and record

Backup to the stage, quit Keynote, copy the build to the session folder, reopen, and re-export to confirm. Log entry in the session's `_log.md`: the instruction in the user's words, the class, what was swept, the measured result, the backups. Memory only when the state changed: the current-state bullet in `memory/kubs.md`; a new class or value goes to `agentkit/rebuild_defects.md` and `deck_reference.json` first, and memory points there.

## The failure classes this pass exists to stop

| Class | One-line trigger | Enforced by |
| --- | --- | --- |
| Reference geometry re-derived | an element that exists elsewhere in the deck is created or replaced | the values file; the band and chart checks |
| A standing requirement dropped | a new instruction on an artifact with existing requirements | preflight 2; the chart check |
| A spec applied to one instance | "all", "every", or a scope the user can see | preflight 1; the pages check |
| Verification that cannot fail | any correctness claim | deckcheck; magnified reads |
| Source structure as the spec | a figure or page built from a book or earlier deck | preflight 3; rule 134 |

## Report

State what is now true (the fixed pages, the sweep, the measured exports), then what waits on the user, then the detail - never the process order. Name the class when the report answers a defect that had recurred, and name the check that would have caught it. The complete inventory is `agentkit/rebuild_defects.md`.
