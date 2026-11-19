"""Definition of done for DatedFileHandler. Rotation runs every second instead of every day,
so 4 s of writing crosses 4 rotations. Run: python -m pytest -q test_dated_log.py"""
import collections
import gzip
import logging
import multiprocessing as mp
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from dated_log import DatedFileHandler  # noqa: E402

SECOND = "%Y-%m-%d_%H-%M-%S"
N_PROC, LINES, SECONDS = 6, 3000, 4
LINE = re.compile(r"^(\d+\.\d{6}) P(\d+) (\d+) x{80}$")
GRACE = 0.5


def _writer(d, idx, t0, caps):
    log = logging.getLogger("t")
    log.setLevel(logging.INFO)
    log.propagate = False
    h = DatedFileHandler(d, "out", datefmt=SECOND, housekeeping=idx < 2, grace_s=GRACE, **caps)
    h.setFormatter(logging.Formatter("%(created)f %(message)s"))
    log.addHandler(h)
    while time.time() < t0:
        time.sleep(0.001)
    for i in range(LINES):
        log.info(f"P{idx} {i} " + "x" * 80)
        time.sleep(SECONDS / LINES)
    h.close()


def _dir_bytes(d):
    total = 0
    for p in d.iterdir():
        try:
            total += 0 if p.is_symlink() else p.stat().st_size
        except FileNotFoundError:
            pass
    return total


def _write_all(d, caps=None):
    """Six processes write; returns the peak directory size seen while they ran."""
    caps = caps or {}
    ctx = mp.get_context("spawn")
    t0 = time.time() + 1.0
    procs = [ctx.Process(target=_writer, args=(str(d), i, t0, caps)) for i in range(N_PROC)]
    for p in procs:
        p.start()
    stop, peak = threading.Event(), [0]

    def sample():
        while not stop.wait(0.02):
            peak[0] = max(peak[0], _dir_bytes(d))
    s = threading.Thread(target=sample)
    s.start()
    for p in procs:
        p.join()
    time.sleep(GRACE + 0.1)                      # the next period's tidy, after the grace
    DatedFileHandler(d, "out", datefmt=SECOND, grace_s=GRACE, **caps).tidy()
    stop.set()
    s.join()
    return peak[0]


def _dated_files(d):
    return sorted(p for p in d.iterdir()
                  if not p.is_symlink() and not p.name.startswith("."))


def _lines(d):
    for p in _dated_files(d):
        opener = gzip.open if p.suffix == ".gz" else open
        with opener(p, "rt") as f:
            for line in f:
                yield p.name, line.rstrip("\n")


@pytest.fixture(scope="module")
def full_run(tmp_path_factory):
    d = tmp_path_factory.mktemp("logs")
    _write_all(d)
    return d


def test_no_line_lost_duplicated_or_misfiled(full_run):
    seen = collections.Counter()
    for name, line in _lines(full_run):
        m = LINE.match(line)
        assert m, f"malformed line in {name}: {line[:80]!r}"
        seen[(int(m[2]), int(m[3]))] += 1
        own_second = time.strftime(SECOND, time.localtime(float(m[1])))
        assert name.startswith(own_second), f"{name} holds a line from {own_second}"
    assert len(seen) == N_PROC * LINES, f"{N_PROC * LINES - len(seen)} lines lost"
    assert max(seen.values()) == 1, "duplicated lines"


def test_closed_periods_are_compressed_and_readable(full_run):
    files = _dated_files(full_run)
    assert len(files) >= SECONDS, files
    assert all(p.suffix == ".gz" for p in files), [p.name for p in files if p.suffix != ".gz"]
    for p in files:
        with gzip.open(p, "rt") as f:            # gzip -t, in Python
            assert LINE.match(f.readline().rstrip("\n"))


def test_link_points_at_newest_period(full_run):
    link = full_run / "out.log"
    assert link.is_symlink()
    newest = max(p.name.removesuffix(".gz") for p in _dated_files(full_run))
    assert Path(link.readlink()).name == newest


def test_disk_bound_holds_under_a_flood(tmp_path):
    day_cap, archive_cap = 30_000, 100_000       # bytes; the flood writes ~1.9 MB
    peak = _write_all(tmp_path, {"day_cap_mb": day_cap / 2**20,
                                 "archive_cap_mb": archive_cap / 2**20})
    # Production (daily files, 120 s grace): archive_cap + 2 * day_cap. Per-second files with
    # a 0.5 s grace can leave one more closed file raw until the next tidy, so 3 * day_cap here.
    bound = archive_cap + 3 * day_cap
    assert peak <= bound, f"peak {peak} > bound {bound}"
    assert _dir_bytes(tmp_path) <= archive_cap + day_cap


@pytest.mark.skipif(shutil.which("rsync") is None, reason="rsync not installed")
def test_backup_pattern_picks_up_every_dated_file(full_run, tmp_path):
    # The Mac-side command, with a local path standing in for chaehan@vm:/var/log/fastapi_app/
    subprocess.run(["rsync", "-a", "--include=20??-??-??*.log*", "--exclude=*",
                    f"{full_run}/", f"{tmp_path}/"], check=True)
    for gz in tmp_path.glob("*.log.gz"):         # the .gz supersedes a raw copy of the same day
        gz.with_suffix("").unlink(missing_ok=True)
    source = {p.name for p in _dated_files(full_run)}
    copied = {p.name for p in tmp_path.iterdir()}
    assert copied == source, (source ^ copied)
