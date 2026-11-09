#!/usr/bin/env python3
"""Render the Life Overview chart: your numbers that moved, two cards per row.

Usage:
    python life_widgets.py <spec.json> <out.png>

Chaehan chose the shape of the 2026-11-09 variant B ("how far you have come")
and then narrowed it: "only important or distinct changes like DPS and LDL with
data vis. the rest is useless just take the top summaries not these stupid
simple data points". So the chart holds measures only, never dates, deadlines
or firsts, and each card is one of two kinds:

  with "vis"  the summary on top (the value now in large type, the change as a
              pill, the earlier value) and B's chart under it: "line" draws the
              dated series with a dot per reading, the best and the latest
              labelled; "bars" draws the earlier and the current value side by
              side with their dates
  no "vis"    the summary alone

Spec shape:
{
  "title": "How far you have come", "subtitle": "...",
  "widgets": [
    {"goal": "Health", "label": "Distance per stroke", "value": 1.01,
     "unit": "m per stroke", "note": "best, 2026-10-20", "before": 0.82,
     "before_date": "2026-02-25", "better": "higher", "vis": "line",
     "series": [["2026-02-25", 0.82], ["2026-10-20", 1.01], ["2026-11-06", 0.92]]},
    {"goal": "Health", "label": "LDL cholesterol", "value": 67, "unit": "mg/dL",
     "date": "2026-10-20", "before": 143, "before_date": "2026-04-23",
     "better": "lower", "vis": "bars"},
    {"goal": "Health", "label": "Perceived effort at the same 400 m",
     "value": 6, "unit": "out of 10", "before": 8, "better": "lower"}
  ]
}

The change in percent is computed here, never written into the spec. Colours
follow B: each card takes the next colour of the palette, and an earlier value
that was worse is drawn red. Requires Pillow (socrates env) and the Apple SD
Gothic Neo font.
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
W, MARGIN, GAP, PAD = 1200, 36, 24, 28
COL = (W - 2 * MARGIN - GAP) // 2
INK, GREY, FAINT, CARD, EDGE, WHITE = "#17222E", "#5B6B7B", "#8A99AA", "#F6F8FB", "#E4EBF4", "#FFFFFF"
GOOD, WORSE = "#15803D", "#E11D48"
PALETTE = ["#2563EB", "#15803D", "#0F766E", "#7C3AED", "#B45309", "#DB2777"]
SUMMARY_H, VIS_H = 250, 500


def number(v: float) -> str:
    return f"{v:g}"


def short(iso: str) -> str:
    return date.fromisoformat(iso).strftime("%b %-d")


def improved(w: dict) -> bool:
    up = w["value"] > w["before"]
    return up == (w.get("better", "higher") == "higher")


def pill(draw, x_right, y, text, bg):
    f = font(30, BOLD)
    w = draw.textlength(text, font=f)
    draw.rounded_rectangle([x_right - w - 28, y, x_right, y + 46], radius=18, fill=bg)
    draw.text((x_right - w - 14, y + 23), text, font=f, fill=WHITE, anchor="lm")


def summary(draw, w, x, y, colour):
    draw.text((x + PAD, y + PAD), w["label"], font=font(32, BOLD), fill=INK)
    draw.text((x + COL - PAD, y + PAD + 4), w["goal"], font=font(28, SEMI), fill=colour, anchor="ra")
    value = number(w["value"])
    vy = y + 84
    draw.text((x + PAD, vy), value, font=font(84, BOLD), fill=colour)
    vw = draw.textlength(value, font=font(84, BOLD))
    if w.get("unit"):
        draw.text((x + PAD + vw + 12, vy + 50), w["unit"], font=font(28), fill=GREY)
    if w.get("before") not in (None, 0):
        change = (w["value"] - w["before"]) / abs(w["before"]) * 100
        sign = "+" if change > 0 else "-"
        pill(draw, x + COL - PAD, vy + 18, f"{sign}{abs(change):.0f}%", GOOD if improved(w) else WORSE)
        was = f"was {number(w['before'])}" + (f" on {short(w['before_date'])}" if w.get("before_date") else "")
        if w.get("note"):
            was = f"{w['note']}, {was}"
        f = font(28)
        while draw.textlength(was, font=f) > COL - 2 * PAD and f.size > 24:
            f = font(f.size - 1)
        draw.text((x + PAD, vy + 104), was, font=f, fill=GREY)


def line_chart(draw, w, x, y0, y1, colour):
    """B's series chart: a dot per reading, the best and the latest labelled."""
    series = w["series"]
    x0, x1 = x + PAD + 14, x + COL - PAD - 14
    ords = [date.fromisoformat(d).toordinal() for d, _ in series]
    vals = [v for _, v in series]
    lo, hi = min(vals), max(vals)
    span = max(hi - lo, 1e-9)
    sx = lambda o: x0 + (o - ords[0]) / max(ords[-1] - ords[0], 1) * (x1 - x0)
    sy = lambda v: y1 - (v - lo) / span * (y1 - y0)
    pts = [(sx(o), sy(v)) for o, v in zip(ords, vals)]
    draw.line(pts, fill=colour, width=5, joint="curve")
    for px, py in pts:
        draw.ellipse([px - 6, py - 6, px + 6, py + 6], fill=colour)
    best = vals.index(hi if w.get("better", "higher") == "higher" else lo)
    bx, by = pts[best]
    draw.ellipse([bx - 12, by - 12, bx + 12, by + 12], fill=colour)
    draw.text((bx, by - 20), number(vals[best]), font=font(32, BOLD), fill=colour, anchor="md")
    if best != len(vals) - 1:
        lx, ly = pts[-1]
        draw.text((lx, ly + 18), number(vals[-1]), font=font(30, BOLD), fill=colour, anchor="ma")
    draw.text((x0, y1 + 56), short(series[0][0]), font=font(28), fill=GREY, anchor="la")
    draw.text((x1, y1 + 56), short(series[-1][0]), font=font(28), fill=GREY, anchor="ra")


def bar_chart(draw, w, x, y0, y1, colour):
    """B's before-and-after bars: the earlier value red when it was worse."""
    pairs = [(w["before"], w.get("before_date"), WORSE if improved(w) else colour),
             (w["value"], w.get("date"), colour if improved(w) else WORSE)]
    top = max(v for v, _, _ in pairs)
    bw = 130
    for i, (v, d, c) in enumerate(pairs):
        cx = x + COL * (1 + 2 * i) / 4
        h = (y1 - y0 - 40) * v / top
        draw.rounded_rectangle([cx - bw / 2, y1 - h, cx + bw / 2, y1], radius=10, fill=c)
        draw.text((cx, y1 - h - 8), number(v), font=font(34, BOLD), fill=c, anchor="md")
        if d:
            draw.text((cx, y1 + 14), short(d), font=font(28), fill=GREY, anchor="ma")


def render(spec: dict, out: Path) -> None:
    widgets = spec["widgets"]
    rows = [widgets[i:i + 2] for i in range(0, len(widgets), 2)]
    heights = [VIS_H if any(w.get("vis") for w in row) else SUMMARY_H for row in rows]
    head = 170
    img = Image.new("RGB", (W, head + sum(h + GAP for h in heights) + MARGIN), WHITE)
    draw = ImageDraw.Draw(img)
    draw.text((MARGIN, 40), spec["title"], font=font(52, BOLD), fill=INK)
    if spec.get("subtitle"):
        draw.text((MARGIN, 108), spec["subtitle"], font=font(30), fill=GREY)
    y, n = head, 0
    for row, h in zip(rows, heights):
        for i, w in enumerate(row):
            x = MARGIN + i * (COL + GAP)
            colour = PALETTE[n % len(PALETTE)]
            n += 1
            card_h = VIS_H if w.get("vis") else SUMMARY_H
            draw.rounded_rectangle([x, y, x + COL, y + card_h], radius=22, fill=CARD, outline=EDGE, width=2)
            summary(draw, w, x, y, colour)
            if w.get("vis") == "line" and len(w.get("series") or []) >= 3:
                line_chart(draw, w, x, y + 290, y + 400, colour)
            elif w.get("vis") == "bars":
                bar_chart(draw, w, x, y + 270, y + 430, colour)
        y += h + GAP
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
