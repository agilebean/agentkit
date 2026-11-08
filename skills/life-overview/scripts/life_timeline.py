#!/usr/bin/env python3
"""Render a phone-readable timeline chart (PNG) for a Life Overview note.

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

Each row is a lane: its label on its own line, then a full-width track. A
lane's colour comes from its position (fixed palette order), so "color" in the
spec is ignored. Open bars render as a pale tint with an outline in the lane
colour; solid bars as full colour. Milestones render as diamonds: green = done,
hollow = open, red = decision. Labels that do not fit inside a bar are packed
on lines under the track, so "text_pos", "offset" and "label_above" are
ignored. Requires Pillow (socrates env).
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Phone-first layout (Chaehan, 2026-11-07: "improve the chart to modern design
# and better readability on a small device"). The PNG is 1200 px wide, which a
# 390 pt phone screen shows at ~1:1 on a 3x display; at that scale 30 px reads
# as ~10 pt, so no text is smaller than 28 px.
W = 1200
S = 3  # supersampling factor: everything is drawn at S× and downscaled once
# at the end. PIL's 1× rasterizer breaks small Helvetica Neue joints (the 'r'
# arm collapses into a stub - caught in the first post-Arial render, 2026-10-06).
PAD = 56
X0, X1 = PAD, W - PAD
BAR_H = 52
LINE_H = 40  # one line of outside labels under a track
BG = "#FFFFFF"
GRID = "#ECECEA"
TEXT = "#1B1B1A"
MUTED = "#52514E"
TODAY_INK = "#1B1B1A"
DECISION = "#D03B3B"  # status red, reserved for decisions, always labelled
DONE = "#0CA30C"
# Lane colours in fixed order (dataviz reference categorical palette, light
# mode; validated 2026-11-07: CVD worst adjacent dE 9.1, normal-vision 19.6).
PALETTE = ["#2A78D6", "#EB6834", "#1BAF7A", "#EDA100", "#E87BA4", "#6250D6", "#008300"]

# Font candidates in preference order; a tuple carries the TTC face index.
# Arial never appears here - banned outright (RULES.md rule 115).
FONTS = {
    True: [
        ("/System/Library/Fonts/HelveticaNeue.ttc", 1),  # Helvetica Neue Bold
        ("/System/Library/Fonts/Helvetica.ttc", 1),      # Helvetica Bold
        "/System/Library/Fonts/SFNS.ttf",
    ],
    False: [
        ("/System/Library/Fonts/HelveticaNeue.ttc", 0),  # Helvetica Neue Regular
        ("/System/Library/Fonts/Helvetica.ttc", 0),      # Helvetica Regular
        "/System/Library/Fonts/SFNS.ttf",
    ],
}


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    for entry in FONTS[bold]:
        path, index = entry if isinstance(entry, tuple) else (entry, 0)
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size=size * S, index=index)
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


class ScaleDraw:
    """ImageDraw proxy that scales coordinates, stroke widths and radii by S,
    so the page rasterizes at S× and is downscaled once (supersampling)."""

    def __init__(self, draw, s):
        self._d, self._s = draw, s

    def _xy(self, xy):
        if isinstance(xy[0], (list, tuple)):
            return [tuple(v * self._s for v in p) for p in xy]
        return tuple(v * self._s for v in xy)

    def _kw(self, kw):
        for k in ("width", "radius"):
            if isinstance(kw.get(k), (int, float)):
                kw[k] = kw[k] * self._s
        return kw

    def text(self, xy, *a, **kw):
        return self._d.text(self._xy(xy), *a, **kw)

    def textbbox(self, xy, *a, **kw):
        box = self._d.textbbox(self._xy(xy), *a, **kw)
        return tuple(v / self._s for v in box)

    def rectangle(self, xy, *a, **kw):
        return self._d.rectangle(self._xy(xy), *a, **self._kw(kw))

    def rounded_rectangle(self, xy, *a, **kw):
        return self._d.rounded_rectangle(self._xy(xy), *a, **self._kw(kw))

    def line(self, xy, *a, **kw):
        return self._d.line(self._xy(xy), *a, **self._kw(kw))

    def polygon(self, xy, *a, **kw):
        return self._d.polygon(self._xy(xy), *a, **self._kw(kw))


def text_w(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def luminance(hex_color: str) -> float:
    def ch(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(v) for v in rgb(hex_color))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def wrap(draw, text: str, font, width: float) -> list[str]:
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if cur and text_w(draw, trial, font) > width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    return lines + ([cur] if cur else [])


def shade(hex_color: str, factor: float) -> str:
    """The colour darkened toward black by factor (0 = unchanged)."""
    return "#%02X%02X%02X" % tuple(round(c * (1 - factor)) for c in rgb(hex_color))


def diamond(d, x, y, r, style):
    pts = [(x, y - r), (x + r, y), (x, y + r), (x - r, y)]
    if style == "done":
        d.polygon(pts, fill=DONE)
    elif style == "decision":
        d.polygon(pts, fill=DECISION)
    else:
        d.polygon(pts, fill=BG, outline=MUTED, width=3)


def pack(labels: list[dict], draw, font) -> int:
    """Place outside labels on lines under the track, left to right, without overlap.
    Each label gets "x" (left edge) and "level"; returns the number of lines used."""
    ends: list[float] = []
    for lab in sorted(labels, key=lambda l: l["cx"]):
        w = text_w(draw, lab["text"], font)
        x = min(max(lab["cx"] - w / 2, X0), X1 - w)
        level = next((i for i, e in enumerate(ends) if x >= e + 20), len(ends))
        if level == len(ends):
            ends.append(0)
        ends[level] = x + w
        lab["x"], lab["w"], lab["level"] = x, w, level
    return len(ends)


def main() -> int:
    spec_path, out_path = sys.argv[1], sys.argv[2]
    spec = json.loads(Path(spec_path).read_text())
    rows = spec["rows"]
    start, end = parse(spec["start"]), parse(spec["end"])
    today = parse(spec["today"]) if spec.get("today") else None
    span = (end - start).days

    def x_of(d: date) -> float:
        return X0 + (d - start).days / span * (X1 - X0)

    probe = ScaleDraw(ImageDraw.Draw(Image.new("RGB", (10, 10))), S)
    f_title = load_font(46, True)
    f_sub = load_font(30)
    f_lane = load_font(32, True)
    f_in = load_font(28, True)
    f_out = load_font(28)
    f_axis = load_font(28)
    f_leg = load_font(28)

    # Layout pass: the title's lines, each lane's packed labels, the canvas height.
    title_lines = wrap(probe, spec["title"], f_title, X1 - X0)
    y = 48 + len(title_lines) * 58 + (44 if spec.get("subtitle") else 0) + 28
    axis_y = y + 40  # month labels sit above this line
    y = axis_y + 28
    lanes = []
    for i, row in enumerate(rows):
        color = PALETTE[i % len(PALETTE)]
        header_y = y
        track_y = header_y + 48
        labels, inside = [], []
        for item in row["items"]:
            text = item.get("text", "")
            if item["kind"] == "bar":
                xs, xe = x_of(parse(item["start"])), x_of(parse(item["end"]))
                if text and text_w(probe, text, f_in) <= xe - xs - 28:
                    inside.append(item)
                elif text:
                    labels.append({"text": text, "cx": (xs + xe) / 2, "style": "bar"})
            elif text:
                labels.append({"text": text, "cx": x_of(parse(item["date"])),
                               "style": item.get("style", "open")})
        levels = pack(labels, probe, f_out)
        lane_h = 48 + BAR_H + (12 + levels * LINE_H if levels else 0) + 36
        lanes.append({"row": row, "color": color, "header_y": header_y,
                      "track_y": track_y, "labels": labels, "inside": inside})
        y += lane_h
    chart_bottom = y - 20

    used = {"solid": False, "open": False, "done": False, "decision": False, "milestone": False}
    for row in rows:
        for item in row["items"]:
            if item["kind"] == "bar":
                used["solid" if item.get("style", "solid") == "solid" else "open"] = True
            else:
                st = item.get("style", "open")
                used[st if st in ("done", "decision") else "milestone"] = True
    legend = [(k, t) for k, t in (("solid", "Booked"), ("open", "Open"), ("decision", "Decision"),
                                  ("milestone", "Milestone"), ("done", "Done")) if used[k]]
    legend_lines, lx = 1, X0
    for _, t in legend:
        w = 56 + text_w(probe, t, f_leg) + 36
        if lx + w > X1:
            legend_lines, lx = legend_lines + 1, X0
        lx += w
    H = int(chart_bottom + 36 + legend_lines * 52 + 36)

    img = Image.new("RGB", (W * S, H * S), BG)
    d = ScaleDraw(ImageDraw.Draw(img), S)

    # Title and subtitle.
    ty = 48
    for line in title_lines:
        d.text((X0, ty), line, font=f_title, fill=TEXT)
        ty += 58
    if spec.get("subtitle"):
        d.text((X0, ty + 4), spec["subtitle"], font=f_sub, fill=MUTED)

    # Today's pill sits in the month row; a month label that would touch it, or
    # its left neighbour, is skipped (the subtitle carries the dates).
    pill_box = None
    if today and start <= today <= end:
        x_t = x_of(today)
        pw = text_w(d, "Today", f_in) + 28
        px = min(max(x_t - pw / 2, X0), X1 - pw)
        pill_box = (px, px + pw)
    m = date(start.year, start.month, 1)
    last_right = -1e9
    while m <= end:
        if m >= start:
            x = x_of(m)
            d.line([x, axis_y, x, chart_bottom], fill=GRID, width=2)
            label = m.strftime("%b %Y" if m.month == 1 else "%b")
            lw = text_w(d, label, f_axis)
            clear = x + 8 >= last_right + 16 and x + 8 + lw <= X1
            if pill_box and x + 8 < pill_box[1] + 12 and x + 8 + lw > pill_box[0] - 12:
                clear = False
            if clear:
                d.text((x + 8, axis_y - 6), label, font=f_axis, fill=MUTED, anchor="lb")
                last_right = x + 8 + lw
        m = date(m.year + (m.month == 12), m.month % 12 + 1, 1)

    # Today: a thin line from the month row down, under the bars and every label.
    if pill_box:
        d.line([x_t, axis_y, x_t, chart_bottom], fill=TODAY_INK, width=3)
        d.rounded_rectangle([pill_box[0], axis_y - 42, pill_box[1], axis_y + 2], radius=22, fill=TODAY_INK)
        d.text(((pill_box[0] + pill_box[1]) / 2, axis_y - 20), "Today", font=f_in, fill=BG, anchor="mm")

    for lane in lanes:
        color, track_y = lane["color"], lane["track_y"]
        yc = track_y + BAR_H / 2
        # Lane label with its colour dot.
        hw = text_w(d, lane["row"]["label"], f_lane)
        d.rectangle([X0 - 4, lane["header_y"] - 2, X0 + 30 + hw + 10, lane["header_y"] + 42], fill=BG)
        d.rounded_rectangle([X0, lane["header_y"] + 10, X0 + 18, lane["header_y"] + 28], radius=9, fill=color)
        d.text((X0 + 30, lane["header_y"] + 19), lane["row"]["label"], font=f_lane, fill=TEXT, anchor="lm")
        # Bars. Neighbours alternate between the lane colour and a darker shade
        # (Chaehan, 2026-11-08: "neighboring bars should not be colored the same").
        bars = sorted((it for it in lane["row"]["items"] if it["kind"] == "bar"), key=lambda it: it["start"])
        for n, item in enumerate(bars):
            color = lane["color"] if n % 2 == 0 else shade(lane["color"], 0.35)
            xs, xe = x_of(parse(item["start"])), x_of(parse(item["end"]))
            xe = max(xe, xs + 14)
            box = [xs + 1, track_y, xe - 1, track_y + BAR_H]  # 2 px surface gap between neighbours
            solid = item.get("style", "solid") == "solid"
            if solid:
                d.rounded_rectangle(box, radius=12, fill=color)
            else:
                d.rounded_rectangle(box, radius=12, fill=blend(color, 0.14), outline=color, width=3)
            if item.get("arrow"):
                tip = min(xe + 16, X1 + 30)
                d.polygon([(tip, yc), (xe - 1, yc - 14), (xe - 1, yc + 14)],
                          fill=color if solid else blend(color, 0.55))
            if item in lane["inside"]:
                ink = BG if solid and luminance(color) < 0.3 else TEXT
                d.text(((xs + xe) / 2, yc), item["text"], font=f_in, fill=ink, anchor="mm")
        # Milestones on the track line.
        for item in lane["row"]["items"]:
            if item["kind"] == "milestone":
                diamond(d, x_of(parse(item["date"])), yc, 17, item.get("style", "open"))
        # Outside labels, each on a white halo so a gridline or the today line never cuts it.
        for lab in lane["labels"]:
            ly = track_y + BAR_H + 12 + lab["level"] * LINE_H
            ink = DECISION if lab["style"] == "decision" else TEXT
            d.rectangle([lab["x"] - 6, ly, lab["x"] + lab["w"] + 6, ly + LINE_H - 4], fill=BG)
            d.text((lab["x"], ly + 2), lab["text"], font=f_out, fill=ink)

    # Legend: only the styles the chart uses, wrapped to the width.
    lx, ly = X0, chart_bottom + 36 + 26
    for kind, label in legend:
        w = 56 + text_w(d, label, f_leg) + 36
        if lx + w > X1:
            lx, ly = X0, ly + 52
        if kind in ("solid", "open"):
            sw = [lx, ly - 14, lx + 44, ly + 14]
            if kind == "solid":
                d.rounded_rectangle(sw, radius=8, fill=MUTED)
            else:
                d.rounded_rectangle(sw, radius=8, fill=blend(MUTED, 0.14), outline=MUTED, width=3)
        else:
            diamond(d, lx + 22, ly, 15, "done" if kind == "done" else "decision" if kind == "decision" else "open")
        d.text((lx + 56, ly), label, font=f_leg, fill=MUTED, anchor="lm")
        lx += w

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    img = img.resize((W, H), Image.LANCZOS)
    img.save(out_path)
    print(f"wrote {out_path} ({W}x{H})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
