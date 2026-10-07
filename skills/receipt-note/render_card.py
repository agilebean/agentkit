#!/usr/bin/env python3
"""Render a booking/confirmation card to a tight-cropped PNG.

The card is the visual placed at the top of an Evernote note made from a
receipt or confirmation (see SKILL.md). It carries the fields the user looks
for later: the name, the dates, the room or class, and the price.

Usage:
    python3 render_card.py --spec card.json --out card.png [--width 900] [--pad 24]

Spec (JSON):
    {
      "title":    "Imperial Hotel Osaka",
      "subtitle": "Booking.com confirmation 5143123603 - booked 2026-10-07",
      "rows": [["Check-in", "Fri, Dec 4, 2026 (14:00-24:00)"], ...],
      "footer":   "Total Y141,000 paid"
    }

rows are [label, value] pairs; any row may be ["", "text"] for a wide line.
Arial is never used (agentkit RULES.md rule 115): Helvetica Neue first.
"""
import argparse
import json
import os
import subprocess
import sys

from PIL import Image, ImageChops

BROWSER = os.environ.get(
    "CARD_BROWSER", "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
)
SCALE = 2  # device pixel ratio, so the PNG is crisp in Evernote


def build_html(spec: dict, width: int) -> str:
    rows = ""
    for label, value in spec.get("rows", []):
        label = str(label)
        value = str(value)
        if label:
            rows += (
                f'<div class="row"><div class="label">{label}</div>'
                f'<div class="value">{value}</div></div>'
            )
        else:
            rows += f'<div class="row wide"><div class="value">{value}</div></div>'
    footer = spec.get("footer")
    footer_html = f'<div class="footer">{footer}</div>' if footer else ""
    subtitle = spec.get("subtitle")
    subtitle_html = f'<div class="subtitle">{subtitle}</div>' if subtitle else ""
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
  * {{ box-sizing: border-box; }}
  body {{ margin:0; background:#ffffff;
         font-family:"Helvetica Neue",Helvetica,sans-serif; color:#1a1a1a; }}
  .card {{ width:{width}px; background:#ffffff; border-top:6px solid #384894;
           padding:26px 30px 22px 30px; }}
  .title {{ font-size:27px; font-weight:600; letter-spacing:-0.2px; }}
  .subtitle {{ margin-top:5px; font-size:13px; color:#6b7280; }}
  .rows {{ margin-top:20px; }}
  .row {{ display:flex; padding:7px 0; border-top:1px solid #ececec; }}
  .row.wide {{ display:block; }}
  .label {{ width:190px; flex:none; font-size:14px; color:#6b7280; }}
  .value {{ font-size:15px; font-weight:500; }}
  .footer {{ margin-top:20px; padding-top:14px; border-top:2px solid #384894;
             font-size:17px; font-weight:600; }}
</style></head><body><div class="card">
  <div class="title">{spec.get('title','')}</div>
  {subtitle_html}
  <div class="rows">{rows}</div>
  {footer_html}
</div></body></html>"""


def find_browser() -> str:
    for cand in (BROWSER, "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                 "/Applications/Chromium.app/Contents/MacOS/Chromium"):
        if os.path.exists(cand):
            return cand
    sys.exit("no Chromium-family browser found; set CARD_BROWSER")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=900)
    ap.add_argument("--pad", type=int, default=0, help="white margin kept around the card, px")
    args = ap.parse_args()

    with open(args.spec) as fh:
        spec = json.load(fh)

    stage = os.environ.get("TMPDIR", "/tmp").rstrip("/") + "/receipt_card"
    os.makedirs(stage, exist_ok=True)
    html_path = os.path.join(stage, "card.html")
    with open(html_path, "w") as fh:
        fh.write(build_html(spec, args.width))

    shot = os.path.join(stage, "card_raw.png")
    subprocess.run(
        [find_browser(), "--headless", "--disable-gpu", "--hide-scrollbars",
         f"--force-device-scale-factor={SCALE}", f"--screenshot={shot}",
         f"--window-size={args.width},2400", f"file://{html_path}"],
        check=True, capture_output=True,
    )

    im = Image.open(shot).convert("RGB")
    bg = Image.new("RGB", im.size, (255, 255, 255))
    box = ImageChops.difference(im, bg).getbbox()
    if box is None:
        sys.exit("card rendered blank")
    box = (max(0, box[0] - args.pad * SCALE), max(0, box[1] - args.pad * SCALE),
           min(im.width, box[2] + args.pad * SCALE), min(im.height, box[3] + args.pad * SCALE))
    out = im.crop(box)
    out.save(args.out)
    print(json.dumps({"out": args.out, "width": out.width, "height": out.height,
                      "bytes": os.path.getsize(args.out)}))


if __name__ == "__main__":
    main()
