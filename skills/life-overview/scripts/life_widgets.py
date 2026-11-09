#!/usr/bin/env python3
"""Render the Life Overview chart: two curves of your numbers that moved, side by side.

Usage:
    python life_widgets.py <spec.json> <out.png>

Chaehan chose the cards of the 2026-11-09 variant B ("how far you have come")
and narrowed them the same day: "only important or distinct changes like DPS
and LDL with data vis", "I told you only the first two. it is too big the goal
is quality over quantity so make the vertically shortest chart possible",
"show the curve for LDL not stupid bar charts ... you need 2-3 data points in
the past to show the trend change" and, for distance per stroke, "the 0.92! is
useless your point was increase so show the min on the left with number", then
"ideally for the charts, it should make a baseline from 3 data points so it is
not a random pick. both for dps and ldl".

So the chart is one row of two cards and nothing above them. Each card holds
its measure's name, its best value in large type, the change from the baseline
as a pill, and the curve of every dated reading. The baseline is the mean of
the three oldest readings in the series, drawn as a dashed line with its number
at the left; only the baseline and the best reading carry numbers, and the
first and last dates sit under the curve. Everything shown is computed here
from the series, so the spec holds the readings and nothing derived.

Spec shape:
{
  "widgets": [
    {"goal": "Health", "label": "Distance per stroke", "unit": "m per stroke",
     "better": "higher", "source": "...", "series": [["2026-02-25", 0.82], ...]},
    {"goal": "Health", "label": "LDL cholesterol", "unit": "mg/dL",
     "better": "lower", "source": "...", "series": [["2025-10-14", 151], ...]}
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


# 1200 px wide: a 390 pt phone screen shows it at ~1:1 on a 3x display, so no
# text is set below 28 px.
W, MARGIN, GAP, PAD = 1200, 24, 24, 26
COL = (W - 2 * MARGIN - GAP) // 2
CARD_H = 380
INK, GREY, CARD, EDGE, WHITE, GOOD = "#17222E", "#5B6B7B", "#F6F8FB", "#E4EBF4", "#FFFFFF", "#15803D"
PALETTE = ["#2563EB", "#0F766E"]


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

    draw.rounded_rectangle([x, y, x + COL, y + CARD_H], radius=22, fill=CARD, outline=EDGE, width=2)
    draw.text((x + PAD, y + PAD - 4), w["label"], font=font(32, BOLD), fill=INK)
    draw.text((x + COL - PAD, y + PAD), w["goal"], font=font(28, SEMI), fill=colour, anchor="ra")

    vy = y + 66
    draw.text((x + PAD, vy), number(best), font=font(72, BOLD), fill=colour)
    vw = draw.textlength(number(best), font=font(72, BOLD))
    draw.text((x + PAD + vw + 10, vy + 40), w.get("unit", ""), font=font(28), fill=GREY)
    change = (best - baseline) / abs(baseline) * 100
    text = f"{'+' if change > 0 else '-'}{abs(change):.0f}%"
    f = font(30, BOLD)
    tw = draw.textlength(text, font=f)
    xr = x + COL - PAD
    draw.rounded_rectangle([xr - tw - 28, vy + 16, xr, vy + 62], radius=18, fill=GOOD)
    draw.text((xr - tw - 14, vy + 39), text, font=f, fill=WHITE, anchor="lm")

    # The curve: room at the left for the baseline's number, above and below for the best.
    x0, x1 = x + PAD + 72, x + COL - PAD - 56
    y0, y1 = y + 206, y + 290
    ords = [date.fromisoformat(d).toordinal() for d, _ in series]
    lo, hi = min(vals), max(vals)
    sx = lambda o: x0 + (o - ords[0]) / max(ords[-1] - ords[0], 1) * (x1 - x0)
    sy = lambda v: y1 - (v - lo) / max(hi - lo, 1e-9) * (y1 - y0)
    pts = [(sx(o), sy(v)) for o, v in zip(ords, vals)]
    by = sy(baseline)
    for dx in range(int(x0), int(x1), 22):  # the baseline, dashed
        draw.line([(dx, by), (min(dx + 12, x1), by)], fill=GREY, width=3)
    draw.text((x0 - 12, by), number(baseline), font=font(30, BOLD), fill=GREY, anchor="rm")
    draw.line(pts, fill=colour, width=5, joint="curve")
    for px, py in pts:
        draw.ellipse([px - 6, py - 6, px + 6, py + 6], fill=colour)
    for i in (best_i,):
        px, py = pts[i]
        draw.ellipse([px - 11, py - 11, px + 11, py + 11], fill=colour)
        if vals[i] == hi:  # the high reading carries its number above the dot
            draw.text((px, py - 18), number(vals[i]), font=font(30, BOLD), fill=colour, anchor="md")
        else:  # the low one beside it, so the dates below stay clear: outward at an end, else inward
            right = i == len(vals) - 1 or (i != 0 and px < x + COL / 2)
            draw.text((px + 20 if right else px - 20, py), number(vals[i]), font=font(30, BOLD),
                      fill=colour, anchor="lm" if right else "rm")
    span_years = series[0][0][:4] != series[-1][0][:4]
    draw.text((x + PAD, y + CARD_H - PAD), axis_date(series[0][0], span_years), font=font(28),
              fill=GREY, anchor="ld")
    draw.text((x + COL - PAD, y + CARD_H - PAD), axis_date(series[-1][0], span_years), font=font(28),
              fill=GREY, anchor="rd")


def render(spec: dict, out: Path) -> None:
    widgets = spec["widgets"][:2]
    img = Image.new("RGB", (W, CARD_H + 2 * MARGIN), WHITE)
    draw = ImageDraw.Draw(img)
    for i, w in enumerate(widgets):
        card(draw, w, MARGIN + i * (COL + GAP), MARGIN, PALETTE[i % len(PALETTE)])
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
