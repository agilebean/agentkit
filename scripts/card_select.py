#!/usr/bin/env python3
"""Select the cards a note says (build spec step 2).

The fill call keeps every fact it finds: asked to skip facts that change
nothing, it skipped 0 of 26 in the pilot. So this script selects. A card whose
fact Chaehan stated himself (`said` filled) and that adds nothing he can do or
gets (`so` and `do` empty) tells him what he already knows: it moves to cut.tsv
beside cards.tsv with the reason "known". Cards of the section "What went well"
stay, because that section retells what Chaehan did.

Run it after card_check.py, which empties a `so` that repeats its fact.

    python3 scripts/card_select.py <build>/cards.tsv
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

_spec = importlib.util.spec_from_file_location("card_check", Path(__file__).resolve().parent / "card_check.py")
cc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cc)

EXEMPT = ("what went well",)


def reason(card: dict) -> str | None:
    if card["section"].strip().lower() in EXEMPT:
        return None
    if card["said"] and not card["so"] and not card["do"]:
        return "known"
    return None


def select_file(path: Path) -> tuple[list[dict], list[dict]]:
    """Move the known cards from cards.tsv to cut.tsv; return (kept, cut)."""
    path = Path(path)
    kept, cut = [], []
    for card in cc.read_cards(path):
        why = reason(card)
        if why:
            cut.append(card | {"reason": why})
        else:
            kept.append(card)
    if cut:
        cut_path = path.with_name("cut.tsv")
        cc.write_cards(cut_path, cc.read_cards(cut_path) + cut, extra=("reason",))
        cc.write_cards(path, kept)
    return kept, cut


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cards", type=Path, help="the build folder's cards.tsv")
    a = ap.parse_args(argv)
    kept, cut = select_file(a.cards)
    for c in cut:
        print(f"  cut {c['id']} ({c['reason']}): {c['thing']} {c['fact']}".rstrip())
    print(f"card_select: {len(kept)} kept, {len(cut)} cut to {a.cards.with_name('cut.tsv')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
