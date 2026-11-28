#!/usr/bin/env python3
"""Build one claim PDF: a patient's note page in front, the scanned pages behind it.

Usage:
    python3 claim_pdf.py spec.json out.pdf

Spec (JSON):
{
  "title": "PATIENT'S NOTE ON THE ENCLOSED INVOICES",
  "rows": [["Patient", "NAME, born YYYY-MM-DD"], ["Clinic", "..."], ["Physician", "..."]],
  "invoices": [["Medical receipt, <treatment>", "YYYY-MM-DD", "208,700"], ...],
  "total": "218,700",
  "blocks": [
    "A paragraph on what the invoices cover.",
    {"codes": [["H04.11", "Dry-eye syndrome"], ...]},
    "A paragraph after the codes."
  ],
  "pages": ["receipt.pdf", "prescription.pdf"],
  "offset": [0, 1]          # optional: 0-based pages per file; omit to take all
}
"""
from __future__ import annotations

import json
import sys

import pymupdf
from pymupdf import Rect

W, X, RIGHT = 595, 60, 535


def note_page(doc, spec):
    page = doc.new_page(width=W, height=842)
    y = 70
    page.insert_text((X, y), spec.get("title", "PATIENT'S NOTE ON THE ENCLOSED INVOICES"),
                     fontname="hebo", fontsize=14)
    page.draw_line(pymupdf.Point(X, y + 12), pymupdf.Point(RIGHT, y + 12), color=(0, 0, 0), width=0.8)
    y += 40
    for label, value in spec.get("rows", []):
        page.insert_text((X, y), label, fontname="hebo", fontsize=10)
        page.insert_text((X + 130, y), value, fontname="helv", fontsize=10)
        y += 16

    y += 16
    page.insert_text((X, y), "Invoice", fontname="hebo", fontsize=9.5)
    page.insert_text((X + 250, y), "Date", fontname="hebo", fontsize=9.5)
    page.insert_text((X + 340, y), "Amount (KRW)", fontname="hebo", fontsize=9.5)
    y += 6
    page.draw_line(pymupdf.Point(X, y), pymupdf.Point(RIGHT, y), color=(0, 0, 0), width=0.7)
    y += 17
    for desc, date, amount in spec.get("invoices", []):
        page.insert_text((X, y), desc, fontname="helv", fontsize=10)
        page.insert_text((X + 250, y), date, fontname="helv", fontsize=10)
        page.insert_text((X + 340, y), amount, fontname="helv", fontsize=10)
        y += 17
    page.draw_line(pymupdf.Point(X, y - 4), pymupdf.Point(RIGHT, y - 4), color=(0, 0, 0), width=0.7)
    y += 12
    page.insert_text((X, y), "Total", fontname="hebo", fontsize=10)
    page.insert_text((X + 340, y), spec["total"], fontname="hebo", fontsize=10)
    y += 30

    for block in spec.get("blocks", []):
        if isinstance(block, str):
            spare = page.insert_textbox(Rect(X, y, RIGHT, y + 400), block,
                                        fontname="helv", fontsize=10.5, lineheight=1.5)
            y += 400 - spare + 18
        else:
            for code, label in block["codes"]:
                page.insert_text((X + 20, y), code, fontname="hebo", fontsize=10.5)
                page.insert_text((X + 90, y), label, fontname="helv", fontsize=10.5)
                y += 18
            y += 16


def main(spec_path: str, out_path: str) -> None:
    spec = json.loads(open(spec_path, encoding="utf-8").read())
    doc = pymupdf.open()
    note_page(doc, spec)
    offsets = spec.get("offset") or [None] * len(spec["pages"])
    for src, sel in zip(spec["pages"], offsets):
        source = pymupdf.open(src)
        if sel is None:
            doc.insert_pdf(source)
        elif isinstance(sel, int):
            doc.insert_pdf(source, from_page=sel, to_page=sel)
        else:
            doc.insert_pdf(source, from_page=sel[0], to_page=sel[-1])
    doc.save(out_path)
    print(f"{len(doc)} pages -> {out_path}")
    doc.close()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
