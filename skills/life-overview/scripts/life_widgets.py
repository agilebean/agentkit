#!/usr/bin/env python3
"""Render the Life Overview chart: a phone-first grid of widgets, two per row.

Usage:
    python life_widgets.py <spec.json> <out.png>

Chaehan chose this shape on 2026-11-09 from three DeepSeek variants: "I prefer B
but two widgets per row with the top widgets of A merged into it but more
concisely". B showed his numbers that moved; A showed what falls due before the
flight. So the chart holds three kinds of widget, laid out in the order the spec
gives them (his priority order: partner search, health, work, logistics):

  due      something dated ahead of today: the days left in large type, what it
           is, its date and at most one short note
  measure  a number of his that moved: its value now, the change from its
           earlier value as a pill (green when it moved the good way), the
           earlier value with its date, and a line of the series when the
           record holds three or more dated values
  first    a step he named himself: its date and what it was

Spec shape:
{
  "title": "...", "subtitle": "...", "today": "YYYY-MM-DD",
  "widgets": [
    {"kind": "due", "goal": "Health", "label": "Freeze fee ends",
     "date": "2026-11-11", "note": "450000 won a year"},
    {"kind": "measure", "goal": "Health", "label": "Distance per stroke",
     "value": 1.01, "unit": "m per stroke", "date": "2026-10-20",
     "before": 0.82, "before_date": "2026-02-25", "better": "higher",
     "series": [["2026-02-25", 0.82], ["2026-10-20", 1.01]]},
    {"kind": "first", "goal": "Work", "label": "First course since Yonsei",
     "date": "2026-09-28"}
  ]
}

The days left and the change in percent are computed here, never written into
the spec. A widget's colour comes from its goal; a widget next to one of the
same goal gets a darker shade, so neighbours never share a colour. Requires
Pillow (socrates env) and the Apple SD Gothic Neo font, which also sets Hangul.
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
W, MARGIN, GAP = 1200, 36, 24
COL = (W - 2 * MARGIN - GAP) // 2
PAD = 28
INK, GREY, FAINT, CARD, EDGE, WHITE = "#17222E", "#5B6B7B", "#8A99AA", "#F6F8FB", "#E4EBF4", "#FFFFFF"
GOOD, BAD, SOON = "#15803D", "#B91C1C", "#B91C1C"
GOALS = {  # priority order and colour (Chaehan, 2026-11-08)
    "Partner search": "#7C3AED",
    "Health": "#0F766E",
    "Work": "#B45309",
    "Logistics": "#2563EB",
}


def shade(hex_colour: str, factor: float) -> str:
    r, g, b = (int(hex_colour[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02X%02X%02X" % tuple(int(c * factor) for c in (r, g, b))


def wrap(draw: ImageDraw.ImageDraw, text: str, f, width: int) -> list[str]:
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=f) <= width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def number(v: float) -> str:
    return f"{v:g}"


def card(draw, x, y, h, colour, goal):
    draw.rounded_rectangle([x, y, x + COL, y + h], radius=22, fill=CARD, outline=EDGE, width=2)
    draw.rounded_rectangle([x, y, x + 10, y + h], radius=5, fill=colour)
    draw.text((x + COL - PAD, y + PAD), goal, font=font(28, SEMI), fill=colour, anchor="ra")


def pill(draw, x, y, text, bg):
    f = font(30, BOLD)
    w = draw.textlength(text, font=f)
    draw.rounded_rectangle([x, y, x + w + 28, y + 46], radius=18, fill=bg)
    draw.text((x + 14, y + 23), text, font=f, fill=WHITE, anchor="lm")


def draw_due(draw, w, x, y, h, colour, today):
    days = (date.fromisoformat(w["date"]) - today).days
    big = "today" if days == 0 else str(days)
    tone = SOON if 0 <= days <= 7 else colour
    draw.text((x + PAD + 6, y + PAD - 6), big, font=font(96, BOLD), fill=tone, anchor="la")
    if days != 0:
        bw = draw.textlength(big, font=font(96, BOLD))
        draw.text((x + PAD + 6 + bw + 12, y + PAD + 62), "day" if days == 1 else "days",
                  font=font(32, SEMI), fill=tone, anchor="la")
    ty = y + 150
    for line in wrap(draw, w["label"], font(34, BOLD), COL - 2 * PAD)[:2]:
        draw.text((x + PAD + 6, ty), line, font=font(34, BOLD), fill=INK)
        ty += 42
    foot = w["date"] + (f"  ·  {w['note']}" if w.get("note") else "")
    for line in wrap(draw, foot, font(28), COL - 2 * PAD)[:2]:
        draw.text((x + PAD + 6, ty + 4), line, font=font(28), fill=GREY)
        ty += 36


def draw_measure(draw, w, x, y, h, colour):
    draw.text((x + PAD + 6, y + PAD), w["label"], font=font(30, BOLD), fill=INK, anchor="la")
    vy = y + 80
    value = number(w["value"])
    draw.text((x + PAD + 6, vy), value, font=font(88, BOLD), fill=colour, anchor="la")
    vw = draw.textlength(value, font=font(88, BOLD))
    if w.get("unit"):
        draw.text((x + PAD + 6 + vw + 12, vy + 52), w["unit"], font=font(28), fill=GREY, anchor="la")
    if w.get("before") not in (None, 0):
        change = (w["value"] - w["before"]) / abs(w["before"]) * 100
        better = w.get("better", "higher")
        good = (change > 0) == (better == "higher")
        sign = "+" if change > 0 else "-"
        pill(draw, x + COL - PAD - draw.textlength(f"{sign}{abs(change):.0f}%", font=font(30, BOLD)) - 28,
             vy + 16, f"{sign}{abs(change):.0f}%", GOOD if good else BAD)
        was = f"was {number(w['before'])}" + (f" on {w['before_date']}" if w.get("before_date") else "")
        draw.text((x + PAD + 6, vy + 106), was, font=font(28), fill=GREY, anchor="la")
    series = w.get("series") or []
    if len(series) >= 3:
        x0, x1 = x + PAD + 6, x + COL - PAD - 10
        y0, y1 = y + 238, y + 290
        days = [date.fromisoformat(d).toordinal() for d, _ in series]
        vals = [v for _, v in series]
        dmin, dmax = min(days), max(days) or 1
        vmin, vmax = min(vals), max(vals)
        sx = lambda d: x0 + (d - dmin) / max(dmax - dmin, 1) * (x1 - x0)
        sy = lambda v: y1 - (v - vmin) / max(vmax - vmin, 1e-9) * (y1 - y0)
        pts = [(sx(d), sy(v)) for d, v in zip(days, vals)]
        draw.line(pts, fill=colour, width=5, joint="curve")
        best = vals.index(max(vals) if w.get("better", "higher") == "higher" else min(vals))
        bx, by = pts[best]
        draw.ellipse([bx - 10, by - 10, bx + 10, by + 10], fill=colour)
        draw.text((x0, y1 + 6), series[0][0], font=font(28), fill=FAINT, anchor="la")
        draw.text((x1, y1 + 6), series[-1][0], font=font(28), fill=FAINT, anchor="ra")


def draw_first(draw, w, x, y, h, colour):
    draw.text((x + PAD + 6, y + PAD), w["date"], font=font(28, SEMI), fill=GREY, anchor="la")
    ty = y + PAD + 52
    for line in wrap(draw, w["label"], font(34, BOLD), COL - 2 * PAD)[:3]:
        draw.text((x + PAD + 6, ty), line, font=font(34, BOLD), fill=INK)
        ty += 44


def natural_height(draw, w) -> int:
    """The card height that fits the widget's content, so no card is padded out."""
    width = COL - 2 * PAD
    if w["kind"] == "due":
        foot = w["date"] + (f"  ·  {w['note']}" if w.get("note") else "")
        return 150 + 42 * len(wrap(draw, w["label"], font(34, BOLD), width)[:2]) \
            + 36 * len(wrap(draw, foot, font(28), width)[:2]) + 24
    if w["kind"] == "measure":
        return 346 if len(w.get("series") or []) >= 3 else 236
    return 80 + 44 * len(wrap(draw, w["label"], font(34, BOLD), width)[:3]) + 20


def render(spec: dict, out: Path) -> None:
    today = date.fromisoformat(spec["today"])
    widgets = spec["widgets"]
    rows = [widgets[i:i + 2] for i in range(0, len(widgets), 2)]
    probe = ImageDraw.Draw(Image.new("RGB", (W, 10)))
    heights = [max(natural_height(probe, w) for w in row) for row in rows]
    head = 170
    height = head + sum(h + GAP for h in heights) + MARGIN
    img = Image.new("RGB", (W, height), WHITE)
    draw = ImageDraw.Draw(img)
    draw.text((MARGIN, 40), spec["title"], font=font(52, BOLD), fill=INK)
    if spec.get("subtitle"):
        draw.text((MARGIN, 108), spec["subtitle"], font=font(30), fill=GREY)
    y, previous = head, None
    for row, h in zip(rows, heights):
        for i, w in enumerate(row):
            x = MARGIN + i * (COL + GAP)
            base = GOALS.get(w["goal"], "#475569")
            colour = shade(base, 0.72) if previous == w["goal"] else base
            previous = None if previous == w["goal"] and colour != base else w["goal"]
            card(draw, x, y, h, colour, w["goal"])
            {"due": lambda: draw_due(draw, w, x, y, h, colour, today),
             "measure": lambda: draw_measure(draw, w, x, y, h, colour),
             "first": lambda: draw_first(draw, w, x, y, h, colour)}[w["kind"]]()
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
