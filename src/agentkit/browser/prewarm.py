"""Pre-download the chromedriver matching the installed or running browser.

Run as ``python -m agentkit.browser.prewarm``. Meant for a scheduled job so a
browser upgrade is absorbed before the next automation run, instead of the first
run paying for the download.
"""

from __future__ import annotations

import argparse
import logging
import sys

from agentkit.browser._driver import (
    prefetch_chromedriver_for_browser,
    resolve_browser_major,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Pre-download the chromedriver matching the browser."
    )
    parser.add_argument(
        "--debugger-address",
        default=None,
        help="CDP address of a running browser (preferred when present).",
    )
    parser.add_argument(
        "--binary",
        default=None,
        help="Browser binary to inspect when no browser is running.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Download budget in seconds.",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    major = resolve_browser_major(
        debugger_address=args.debugger_address, binary=args.binary
    )
    if major is None:
        print("Could not determine the browser version to match.", file=sys.stderr)
        return 1

    job = prefetch_chromedriver_for_browser(
        debugger_address=args.debugger_address,
        binary=args.binary,
        timeout_s=args.timeout,
    )
    if job is None:  # pragma: no cover - resolve_browser_major already checked
        print("Could not determine the browser version to match.", file=sys.stderr)
        return 1

    try:
        path = job.result()
    except Exception as exc:
        print(f"Prewarm failed: {exc}", file=sys.stderr)
        return 1
    print(f"chromedriver {major} ready: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
