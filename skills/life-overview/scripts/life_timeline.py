#!/usr/bin/env python3
"""Render a horizontal timeline chart (PNG) for a Life Overview note.

Usage:
    python life_timeline.py <spec.json> <out.png>

Spec shape:
{
  "title": "...", "subtitle": "...",
  "start": "YYYY-MM-DD", "end": "YYYY-MM-DD", "today": "YYYY-MM-DD",
  "rows": [
    {"label": "Row label", "items": [
      {"kind": "bar", "start": "...", "end": "...", "text": "...",
       "style": "solid" | "open", "color": "#RRGGBB", "arrow": false},
      {"kind": "milestone", "date": "...", "text": "...",
       "style": "done" | "open" | "decision", "label_above": false}
    ]}
  ]
}

Open bars render as pale fill + colored outline; solid bars as full color.
Milestones render as diamonds: green filled = done, gray hollow = open,
red = decision. Requires Pillow (socrates env).
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W = 1700
GUTTER = 330
X0, X1 = 355, 1650
ROW_H = 92
HEADER_H = 150
BG = "#FFFFFF"
BAND = "#F6F7F9"
GRID = "#D9DEE5"
TEXT = "#1F2933"
MUTED = "#6B7280"
TODAY = "#E03131"
DONE = "#2F9E44"

FONTS = {
    True: [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/System/Library/Fonts/SFNS.ttf",
    ],
    False: [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNS.ttf",
    ],
}


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    for path in FONTS[bold]:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size=size)
            except Exception:
                continue
    return ImageFont.load_default()


def parse(d: str) -> date:
    y, m, dd = (int(x) for x in d.split("-"))
    return date(y, m, dd)


def rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def blend(hex_color: str, alpha: float, bg: str = "#FFFFFF") -> str:
    f, b = rgb(hex_color), rgb(bg)
    return "#%02X%02X%02X" % tuple(
        round(f[i] * alpha + b[i] * (1 - alpha)) for i in range(3)
    )


def text_w(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def dashed_vline(draw, x, y_top, y_bottom, color, dash=9, gap=7, width=3):
    y = y_top
    while y < y_bottom:
        draw.rectangle([x, y, x + width - 1, min(y + dash, y_bottom)], fill=color)
        y += dash + gap


def main() -> int:
    spec_path, out_path = sys.argv[1], sys.argv[2]
    spec = json.loads(Path(spec_path).read_text())
    rows = spec["rows"]
    start, end = parse(spec["start"]), parse(spec["end"])
    today = parse(spec["today"]) if spec.get("today") else None
    span = (end - start).days

    def x_of(d: date) -> float:
        return X0 + (d - start).days / span * (X1 - X0)

    n = len(rows)
    axis_y = HEADER_H + n * ROW_H + 8
    H = axis_y + 140

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    f_title = load_font(32, True)
    f_sub = load_font(17)
    f_row = load_font(20, True)
    f_bar = load_font(15, True)
    f_bar2 = load_font(15)
    f_ms = load_font(14, True)
    f_axis = load_font(15)
    f_leg = load_font(15)

    # header
    d.text((60, 40), spec["title"], font=f_title, fill=TEXT)
    if spec.get("subtitle"):
        d.text((60, 86), spec["subtitle"], font=f_sub, fill=MUTED)

    # row bands + labels
    for i, row in enumerate(rows):
        y_top = HEADER_H + i * ROW_H
        if i % 2 == 1:
            d.rectangle([0, y_top, W, y_top + ROW_H], fill=BAND)
        d.text((GUTTER, y_top + ROW_H / 2), row["label"], font=f_row,
               fill=TEXT, anchor="rm")

    # month gridlines + labels
    months = []
    m = date(start.year, start.month, 1)
    while m <= end:
        months.append(m)
        m = date(m.year + (m.month == 12), m.month % 12 + 1, 1)
    for m in months:
        if m < start:
            continue
        x = x_of(m)
        d.line([x, HEADER_H - 12, x, axis_y], fill=GRID, width=1)
        first_visible = next((mm for mm in months if mm >= start), None)
        label = m.strftime("%b %Y") if m == first_visible else m.strftime("%b")
        d.text((x + 8, axis_y + 10), label, font=f_axis, fill=MUTED)
    d.line([X0 - 10, axis_y, X1, axis_y], fill=GRID, width=2)

    # today marker
    if today and start <= today <= end:
        x_t = x_of(today)
        dashed_vline(d, x_t, HEADER_H - 34, axis_y, TODAY)
        d.text((x_t + 9, HEADER_H - 58), "today", font=load_font(15, True), fill=TODAY)

    # items
    for i, row in enumerate(rows):
        y_c = HEADER_H + i * ROW_H + ROW_H / 2
        for item in row["items"]:
            color = item.get("color", "#4C78A8")
            if item["kind"] == "bar":
                xs, xe = x_of(parse(item["start"])), x_of(parse(item["end"]))
                x_end = xe
                if item.get("arrow"):
                    x_end = xe + 14
                box = [xs, y_c - 17, x_end, y_c + 17]
                if item.get("style", "solid") == "solid":
                    d.rounded_rectangle(box, radius=9, fill=color)
                    inside_fill, inside_font = "#FFFFFF", f_bar
                else:
                    d.rounded_rectangle(box, radius=9, fill=blend(color, 0.16),
                                        outline=color, width=3)
                    inside_fill, inside_font = blend(color, 0.85), f_bar
                label = item.get("text", "")
                pos = item.get("text_pos", "center")
                if label:
                    fits = text_w(d, label, inside_font) <= (x_end - xs) - 22 and (x_end - xs) > 60
                    if pos == "center" and fits:
                        d.text(((xs + x_end) / 2, y_c), label, font=inside_font,
                               fill=inside_fill, anchor="mm")
                    elif pos == "below":
                        d.text(((xs + x_end) / 2, y_c + 20), label, font=f_bar2,
                               fill=TEXT, anchor="ma")
                    elif pos == "above":
                        d.text(((xs + x_end) / 2, y_c - 20), label, font=f_bar2,
                               fill=TEXT, anchor="mb")
                    else:
                        d.text((x_end + 12, y_c), label, font=f_bar2,
                               fill=TEXT, anchor="lm")
                if item.get("arrow"):
                    tip_x = x_end + 13
                    d.polygon([(tip_x, y_c), (x_end - 2, y_c - 11), (x_end - 2, y_c + 11)],
                              fill=color if item.get("style", "solid") == "solid" else blend(color, 0.5))
            else:  # milestone
                x_m = x_of(parse(item["date"]))
                style = item.get("style", "open")
                floating = item.get("offset") == "above"
                y_m = y_c - 30 if floating else y_c
                r = 10 if floating else 13
                if style == "done":
                    d.polygon([(x_m, y_m - r), (x_m + r, y_m), (x_m, y_m + r), (x_m - r, y_m)],
                              fill=DONE)
                    label_fill = "#2B8A3E"
                elif style == "decision":
                    d.polygon([(x_m, y_m - r), (x_m + r, y_m), (x_m, y_m + r), (x_m - r, y_m)],
                              fill=TODAY)
                    label_fill = TODAY
                else:
                    d.polygon([(x_m, y_m - r), (x_m + r, y_m), (x_m, y_m + r), (x_m - r, y_m)],
                              fill="#FFFFFF", outline=MUTED, width=2)
                    label_fill = MUTED
                if item.get("text"):
                    if floating:
                        d.text((x_m + 16, y_m), item["text"], font=f_ms,
                               fill=label_fill, anchor="lm")
                    elif item.get("label_above"):
                        d.text((x_m, y_c - 20), item["text"], font=f_ms,
                               fill=label_fill, anchor="mb")
                    else:
                        d.text((x_m, y_c + 20), item["text"], font=f_ms,
                               fill=label_fill, anchor="ma")

    # legend
    ly = axis_y + 66
    lx = 60
    samples = [
        ("solid", "booked / fixed"),
        ("open", "open / conditional"),
        ("done", "done"),
        ("open-ms", "milestone"),
        ("decision", "decision"),
    ]
    for kind, label in samples:
        if kind in ("solid", "open"):
            if kind == "solid":
                d.rounded_rectangle([lx, ly - 8, lx + 30, ly + 8], radius=5, fill="#4C78A8")
            else:
                d.rounded_rectangle([lx, ly - 8, lx + 30, ly + 8], radius=5,
                                    fill=blend("#4C78A8", 0.16), outline="#4C78A8", width=2)
            lx += 40
        else:
            cx = lx + 12
            if kind == "done":
                d.polygon([(cx, ly - 10), (cx + 10, ly), (cx, ly + 10), (cx - 10, ly)], fill=DONE)
            elif kind == "decision":
                d.polygon([(cx, ly - 10), (cx + 10, ly), (cx, ly + 10), (cx - 10, ly)], fill=TODAY)
            else:
                d.polygon([(cx, ly - 10), (cx + 10, ly), (cx, ly + 10), (cx - 10, ly)],
                          fill="#FFFFFF", outline=MUTED, width=2)
            lx += 30
        d.text((lx, ly), label, font=f_leg, fill=MUTED, anchor="lm")
        lx += text_w(d, label, f_leg) + 44

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    print(f"wrote {out_path} ({W}x{H})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
