"""Standardized quote PDF renaming."""
from __future__ import annotations

from pathlib import Path


def make_quote_filename(date: str, provider: str, price: str | int) -> str:
    if isinstance(price, int):
        price_str = f"${price}"
    else:
        price_str = price if price.startswith("$") else f"${price}"
    price_str = price_str.replace(",", "")
    return f"{date} {provider} Quote {price_str}.pdf"


def _dedup_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    counter = 2
    while True:
        candidate = path.with_name(f"{stem} ({counter}){suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def rename_quote_pdf(
    input_path: str | Path,
    date: str,
    provider: str,
    price: str | int,
    output_dir: str | Path | None = None,
) -> Path:
    src = Path(input_path)
    new_name = make_quote_filename(date, provider, price)
    dst_dir = Path(output_dir) if output_dir else src.parent
    dst = _dedup_path(dst_dir / new_name)
    src.rename(dst)
    return dst
