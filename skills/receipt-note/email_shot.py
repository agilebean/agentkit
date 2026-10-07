#!/usr/bin/env python3
"""Screenshot an email (or a saved web page) to a tight-cropped PNG.

Used by the receipt-note skill: when a confirmation email's own HTML is
available, the note carries the email itself, not a rebuilt card. An .eml
file is parsed for its HTML part; an --html file is rendered as it is.

Usage:
    python3 email_shot.py --eml mail.eml --out shot.png [--width 760] [--pad 8]
    python3 email_shot.py --html page.html --out shot.png [--width 900]

The page is rendered in a Chromium-family browser at the given CSS width with
a device pixel ratio of 2, then cropped to its ink: the empty page below the
message is removed by comparing against the page's own background colour, so
the PNG is the message and nothing else.
"""
import argparse
import email
import email.policy
import json
import os
import subprocess
import sys

from PIL import Image, ImageChops

BROWSER = os.environ.get(
    "CARD_BROWSER", "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
)
SCALE = 2


def find_browser() -> str:
    for cand in (BROWSER, "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                 "/Applications/Chromium.app/Contents/MacOS/Chromium"):
        if os.path.exists(cand):
            return cand
    sys.exit("no Chromium-family browser found; set CARD_BROWSER")


def html_from_eml(path: str) -> str:
    with open(path, "rb") as fh:
        msg = email.message_from_binary_file(fh, policy=email.policy.default)
    html_part = None
    text_part = None
    for part in msg.walk():
        ct = part.get_content_type()
        if ct == "text/html" and html_part is None:
            html_part = part.get_content()
        elif ct == "text/plain" and text_part is None:
            text_part = part.get_content()
    if html_part:
        return html_part
    if text_part:
        return ("<!DOCTYPE html><html><body><pre style=\"white-space:pre-wrap;"
                "font-family:'Helvetica Neue',Helvetica,sans-serif;font-size:14px;"
                "padding:24px\">" + text_part.replace("&", "&amp;")
                .replace("<", "&lt;") + "</pre></body></html>")
    sys.exit(f"{path}: no text/html or text/plain part")


def main() -> None:
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--eml")
    src.add_argument("--html")
    ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=760)
    ap.add_argument("--height", type=int, default=2600, help="render window height, CSS px")
    ap.add_argument("--pad", type=int, default=8, help="margin kept around the ink, px")
    args = ap.parse_args()

    stage = os.environ.get("TMPDIR", "/tmp").rstrip("/") + "/receipt_card"
    os.makedirs(stage, exist_ok=True)
    page = os.path.join(stage, "email.html")
    with open(page, "w") as fh:
        fh.write(html_from_eml(args.eml) if args.eml else open(args.html).read())

    raw = os.path.join(stage, "email_raw.png")
    subprocess.run(
        [find_browser(), "--headless", "--disable-gpu", "--hide-scrollbars",
         "--virtual-time-budget=8000",
         f"--force-device-scale-factor={SCALE}", f"--screenshot={raw}",
         f"--window-size={args.width},{args.height}", f"file://{page}"],
        check=True, capture_output=True,
    )

    im = Image.open(raw).convert("RGB")
    bg_colour = im.getpixel((2, im.height - 2))
    bg = Image.new("RGB", im.size, bg_colour)
    box = ImageChops.difference(im, bg).getbbox()
    if box is None:
        sys.exit("rendered blank")
    box = (max(0, box[0] - args.pad * SCALE), max(0, box[1] - args.pad * SCALE),
           min(im.width, box[2] + args.pad * SCALE), min(im.height, box[3] + args.pad * SCALE))
    out = im.crop(box)
    out.save(args.out)
    print(json.dumps({"out": args.out, "width": out.width, "height": out.height,
                      "bytes": os.path.getsize(args.out)}))


if __name__ == "__main__":
    main()
