#!/usr/bin/env python3
"""Render the Life Overview chart: 2, 4 or 6 curves of the changes that matter, two to a row.

Usage:
    python life_widgets.py <spec.json> <out.png>

Chaehan chose the cards of the 2026-11-09 variant B ("how far you have come")
and narrowed them the same day: "only important or distinct changes like DPS
and LDL with data vis", "I told you only the first two. it is too big the goal
is quality over quantity so make the vertically shortest chart possible",
"show the curve for LDL not stupid bar charts ... you need 2-3 data points in
the past to show the trend change", "show the min on the left with number",
then "ideally for the charts, it should make a baseline from 3 data points so
it is not a random pick. both for dps and ldl". The set of cards is not fixed:
2026-11-10, "the skill should not have hardcoded the content of what is shown!
... it shows 2,4 or 6 of the most important life changes, and compares them
over a longer period of 6-12 monts as the dps and ldl did". The spec decides
which measures; the renderer only lays them out, two to a row, and takes the
number of cards the spec holds: 2, 4 or 6.

Each card holds its measure's name, its best value in large type, the change
from the baseline as a pill, and the curve of every dated reading. The baseline is the mean of
the three oldest readings in the series, drawn as a dashed line with its number
at the left; only the baseline and the best reading carry numbers, and the
first and last dates sit under the curve. Everything shown is computed here
from the series, so the spec holds the readings and nothing derived.

Spec shape (2, 4 or 6 widgets, in priority order):
{
  "widgets": [
    {"goal": "Health", "label": "<measure>", "unit": "<unit>", "better": "higher",
     "source": "<file or note, and the column>", "series": [["2026-02-25", 0.82], ...]},
    {"goal": "Money", "label": "<measure>", "unit": "<unit>", "better": "lower",
     "source": "...", "series": [["2025-10-14", 151], ...]}
  ]
}

Requires Pillow (socrates env) and the Apple SD Gothic Neo font.
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
REG, SEMI, BOLD = 0, 4, 6


def font(size: int, weight: int = REG) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT, size, index=weight)


# 1200 px wide: a 390 pt phone screen shows it at ~1:1 on a 3x display. Half the
# card height of the 2026-11-09 first cut (Chaehan, 2026-11-10: "the vertical
# height of the chart is still too high reduce at least by 50% so you can make
# two rows of more data vis"), so one row of two cards takes 208 px and a second
# row of two more fits in the space the first cut alone used.
W, MARGIN, GAP, PAD = 1200, 12, 20, 22
COL = (W - 2 * MARGIN - GAP) // 2
CARD_H = 186
INK, GREY, CARD, EDGE, WHITE, GOOD = "#17222E", "#5B6B7B", "#F6F8FB", "#E4EBF4", "#FFFFFF", "#15803D"
PALETTE = ["#2563EB", "#0F766E", "#7C3AED", "#B45309", "#BE123C", "#0E7490"]
ROW_GAP = 20


def number(v: float) -> str:
    return f"{v:g}"


def decimals(vals: list[float]) -> int:
    """The baseline is rounded to the precision the readings are given in."""
    return max((len(f"{v:g}".split(".")[1]) if "." in f"{v:g}" else 0) for v in vals)


def axis_date(iso: str, span_years: bool) -> str:
    d = date.fromisoformat(iso)
    return d.strftime("%b %Y") if span_years else d.strftime("%b %-d")


def card(draw, w, x, y, colour):
    series = sorted(w["series"])
    vals = [v for _, v in series]
    higher = w.get("better", "higher") == "higher"
    best_i = vals.index(max(vals) if higher else min(vals))
    best = vals[best_i]
    baseline = round(sum(vals[:3]) / len(vals[:3]), decimals(vals))

    draw.rounded_rectangle([x, y, x + COL, y + CARD_H], radius=16, fill=CARD, outline=EDGE, width=2)
    # A label as long as its measure is shrinks, then ellipses, so it never runs into the goal tag.
    goal_font = font(24, SEMI)
    label, size = w["label"], 28
    room = COL - 2 * PAD - draw.textlength(w["goal"], font=goal_font) - 14
    while size > 18 and draw.textlength(label, font=font(size, BOLD)) > room:
        size -= 2
    while label and draw.textlength(label + "\u2026", font=font(size, BOLD)) > room:
        label = label[:-1]
    if label != w["label"]:
        label += "\u2026"
    draw.text((x + PAD, y + 8), label, font=font(size, BOLD), fill=INK)
    draw.text((x + COL - PAD, y + 12), w["goal"], font=goal_font, fill=colour, anchor="ra")

    vy = y + 38
    draw.text((x + PAD, vy), number(best), font=font(46, BOLD), fill=colour)
    vw = draw.textlength(number(best), font=font(46, BOLD))
    draw.text((x + PAD + vw + 8, vy + 26), w.get("unit", ""), font=font(24), fill=GREY)
    change = (best - baseline) / abs(baseline) * 100
    text = f"{'+' if change > 0 else '-'}{abs(change):.0f}%"
    f = font(24, BOLD)
    tw = draw.textlength(text, font=f)
    xr = x + COL - PAD
    draw.rounded_rectangle([xr - tw - 18, vy + 4, xr, vy + 36], radius=13, fill=GOOD)
    draw.text((xr - tw - 9, vy + 20), text, font=f, fill=WHITE, anchor="lm")

    # The curve: room at the left for the baseline's number, and the best reading
    # is the card's big number already, so the curve carries no second copy of it.
    base_txt = number(baseline)
    gutter = max(52, draw.textlength(base_txt, font=font(22, BOLD)) + 10)
    x0, x1 = x + PAD + gutter, x + COL - PAD - 18
    y0, y1 = y + 102, y + 146
    ords = [date.fromisoformat(d).toordinal() for d, _ in series]
    lo, hi = min(vals), max(vals)
    sx = lambda o: x0 + (o - ords[0]) / max(ords[-1] - ords[0], 1) * (x1 - x0)
    sy = lambda v: y1 - (v - lo) / max(hi - lo, 1e-9) * (y1 - y0)
    pts = [(sx(o), sy(v)) for o, v in zip(ords, vals)]
    by = sy(baseline)
    for dx in range(int(x0), int(x1), 20):  # the baseline, dashed
        draw.line([(dx, by), (min(dx + 11, x1), by)], fill=GREY, width=2)
    draw.text((x0 - 8, by), base_txt, font=font(22, BOLD), fill=GREY, anchor="rm")
    draw.line(pts, fill=colour, width=4, joint="curve")
    for px, py in pts:
        draw.ellipse([px - 4, py - 4, px + 4, py + 4], fill=colour)
    px, py = pts[best_i]
    draw.ellipse([px - 7, py - 7, px + 7, py + 7], fill=colour)
    span_years = series[0][0][:4] != series[-1][0][:4]
    draw.text((x + PAD, y + CARD_H - 8), axis_date(series[0][0], span_years), font=font(22),
              fill=GREY, anchor="ld")
    draw.text((x + COL - PAD, y + CARD_H - 8), axis_date(series[-1][0], span_years), font=font(22),
              fill=GREY, anchor="rd")


def render(spec: dict, out: Path) -> None:
    widgets = spec["widgets"]
    if len(widgets) not in (2, 4, 6):
        raise SystemExit(f"the chart holds 2, 4 or 6 cards, not {len(widgets)}")
    rows = (len(widgets) + 1) // 2
    img = Image.new("RGB", (W, rows * CARD_H + (rows - 1) * ROW_GAP + 2 * MARGIN), WHITE)
    draw = ImageDraw.Draw(img)
    for i, w in enumerate(widgets):
        card(draw, w, MARGIN + (i % 2) * (COL + GAP), MARGIN + (i // 2) * (CARD_H + ROW_GAP),
             PALETTE[i % len(PALETTE)])
    img.save(out)


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__.splitlines()[3].strip())
        return 1
    render(json.loads(Path(argv[1]).read_text(encoding="utf-8")), Path(argv[2]))
    print(f"wrote {argv[2]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
