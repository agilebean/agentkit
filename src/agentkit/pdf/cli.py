"""CLI wrapper for markitdown with status feedback.

Usage:
    python -m agentkit.pdf.cli convert <input.pdf> -o <output.md>
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agentkit.pdf.cli")
    sub = parser.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("convert", help="Convert PDF to markdown via markitdown.")
    c.add_argument("input", help="PDF file path")
    c.add_argument("-o", "--output", required=True, help="Output .md file path")

    r = sub.add_parser("rename", help="Rename a quote PDF to standard format.")
    r.add_argument("input", help="PDF file to rename")
    r.add_argument("--date", required=True, help="ISO date (YYYY-MM-DD)")
    r.add_argument("--provider", required=True, help="Provider name")
    r.add_argument("--price", required=True, help="Price (e.g., 3220 or $3220)")
    r.add_argument("--output-dir", default=None, help="Target directory (default: same dir)")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.cmd == "convert":
        return _cmd_convert(args.input, args.output)

    if args.cmd == "rename":
        from agentkit.pdf.rename import rename_quote_pdf
        result = rename_quote_pdf(
            args.input, args.date, args.provider, args.price, args.output_dir
        )
        print(json.dumps({"renamed_to": str(result)}))
        return 0

    return 1


def _cmd_convert(input_path: str, output_path: str) -> int:
    src = Path(input_path)
    dst = Path(output_path)

    if not src.is_file():
        print(json.dumps({
            "status": "error",
            "input": str(src),
            "error": "Input file not found",
        }), file=sys.stderr)
        return 1

    markitdown_path = shutil.which("markitdown")
    if not markitdown_path:
        print(json.dumps({
            "status": "error",
            "input": str(src),
            "error": "markitdown not found on PATH. Install it or add ~/.local/bin to PATH.",
        }), file=sys.stderr)
        return 1

    proc = subprocess.run(
        [markitdown_path, str(src), "-o", str(dst)],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        print(json.dumps({
            "status": "error",
            "input": str(src),
            "error": proc.stderr.strip() or "markitdown failed",
        }), file=sys.stderr)
        return 1

    if not dst.is_file():
        print(json.dumps({
            "status": "error",
            "input": str(src),
            "error": "Output file not created",
        }), file=sys.stderr)
        return 1

    content = dst.read_text(encoding="utf-8")
    char_count = len(content)

    result: dict = {
        "status": "ok" if char_count > 0 else "empty",
        "input": str(src),
        "output": str(dst),
        "chars": char_count,
    }

    if char_count == 0:
        result["warning"] = "No text extracted \u2014 PDF may be image-only or corrupted"
    elif char_count < 50:
        result["warning"] = f"Very short output ({char_count} chars) \u2014 extraction may be incomplete"

    print(json.dumps(result))
    return 0 if char_count > 0 else 2


if __name__ == "__main__":
    sys.exit(main())
