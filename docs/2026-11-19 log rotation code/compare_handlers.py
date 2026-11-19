"""Six processes write numbered lines through each rotation scheme; count lost, duplicated
and misfiled lines. Usage: python compare_handlers.py [scheme ...]"""
import collections
import gzip
import logging
import logging.handlers
import multiprocessing as mp
import os
import re
import shutil
import sys
import tempfile
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dated_log import DatedFileHandler  # noqa: E402

N_PROC, LINES, SECONDS = 6, 4000, 5
PAD = "x" * 80
LINE = re.compile(r"^(\d+\.\d{6}) P(\d+) (\d+) x{80}$")
SECOND = "%Y-%m-%d_%H-%M-%S"


def make_handler(scheme, d, idx, caps):
    live = str(d / "out.log")
    if scheme == "rotating":
        return logging.handlers.RotatingFileHandler(live, maxBytes=800_000, backupCount=5)
    if scheme == "timed_gzip":
        h = logging.handlers.TimedRotatingFileHandler(live, when="S", interval=1, backupCount=0)
        h.namer = lambda name: name + ".gz"

        def rotator(src, dst):
            with open(src, "rb") as s, gzip.open(dst, "wb") as t:
                shutil.copyfileobj(s, t)
            os.remove(src)
        h.rotator = rotator
        return h
    if scheme.startswith("watched"):
        return logging.handlers.WatchedFileHandler(live)
    if scheme.startswith("dated"):
        return DatedFileHandler(d, "out", datefmt=SECOND, housekeeping=idx < 2, grace_s=0.5, **caps)
    raise ValueError(scheme)


def writer(scheme, d, idx, t0, caps):
    log = logging.getLogger("t")
    log.setLevel(logging.INFO)
    log.propagate = False
    h = make_handler(scheme, Path(d), idx, caps)
    h.setFormatter(logging.Formatter("%(created)f %(message)s"))
    log.addHandler(h)
    while time.time() < t0:
        time.sleep(0.001)
    for i in range(LINES):
        log.info(f"P{idx} {i} {PAD}")
        time.sleep(SECONDS / LINES)
    h.close()


def external_rotator(scheme, d, stop):
    """What logrotate does, every 0.5 s instead of every day."""
    live, n = d / "out.log", 0
    while not stop.wait(0.5):
        n += 1
        arc = d / f"out.log.{n}"
        if scheme == "watched_copytruncate":
            shutil.copyfile(live, arc)
            os.truncate(live, 0)
        else:                                            # create: rename, then a fresh file
            os.rename(live, arc)
            os.close(os.open(live, os.O_CREAT | os.O_WRONLY, 0o640))
            target = arc if scheme == "watched_create_nodelay" else d / f"out.log.{n - 1}"
            if target.exists():                         # delaycompress: previous generation
                with open(target, "rb") as s, gzip.open(f"{target}.gz", "wb") as t:
                    shutil.copyfileobj(s, t)
                os.remove(target)


def dir_bytes(d):
    total = 0
    for p in d.iterdir():
        try:
            if not p.is_symlink():
                total += p.stat().st_size
        except FileNotFoundError:
            pass
    return total


def read_lines(d):
    for p in sorted(d.iterdir()):
        if p.is_symlink() or p.name.startswith("."):
            continue
        opener = gzip.open if p.suffix == ".gz" else open
        with opener(p, "rt", errors="replace") as f:
            for line in f:
                yield p.name, line.rstrip("\n")


def run(scheme, caps=None):
    caps = caps or {}
    d = Path(tempfile.mkdtemp(prefix=f"{scheme}-"))
    stop, peak = threading.Event(), [0]
    t0 = time.time() + 1.0
    procs = [mp.Process(target=writer, args=(scheme, str(d), i, t0, caps)) for i in range(N_PROC)]
    for p in procs:
        p.start()
    rot = None
    if scheme.startswith("watched"):
        (d / "out.log").touch()
        rot = threading.Thread(target=external_rotator, args=(scheme, d, stop))
        rot.start()

    def sample():
        while not stop.wait(0.05):
            peak[0] = max(peak[0], dir_bytes(d))
    sampler = threading.Thread(target=sample)
    sampler.start()
    for p in procs:
        p.join()
    if scheme.startswith("dated"):                       # the next day's tidy, after the grace
        time.sleep(0.6)
        DatedFileHandler(d, "out", datefmt=SECOND, grace_s=0.5, **caps).tidy()
    stop.set()
    sampler.join()
    if rot:
        rot.join()

    found, malformed, misfiled, markers = collections.Counter(), 0, 0, 0
    for name, line in read_lines(d):
        m = LINE.match(line)
        if not m:
            if line.startswith("[pid"):
                markers += 1
            else:
                malformed += 1
            continue
        created, p, i = float(m[1]), int(m[2]), int(m[3])
        found[(p, i)] += 1
        if scheme.startswith("dated") or scheme == "timed_gzip":
            stamp = re.search(r"\d{4}-\d\d-\d\d_\d\d-\d\d-\d\d", name)
            if stamp and stamp[0] != time.strftime(SECOND, time.localtime(created)):
                misfiled += 1
    expected = N_PROC * LINES
    lost = expected - len(found)
    dup = sum(c - 1 for c in found.values())
    files = sum(1 for p in d.iterdir() if not p.is_symlink() and not p.name.startswith("."))
    print(f"{scheme:24} lost {lost:6d} ({100 * lost / expected:5.1f}%)  dup {dup:4d}  "
          f"malformed {malformed:3d}  misfiled {misfiled:5d}  files {files:3d}  "
          f"peak dir {peak[0] / 1e6:6.2f} MB  markers {markers}")
    shutil.rmtree(d)


if __name__ == "__main__":
    mp.set_start_method("spawn")
    schemes = sys.argv[1:] or ["rotating", "timed_gzip", "watched_copytruncate",
                               "watched_create_nodelay", "watched_create", "dated"]
    print(f"{N_PROC} processes x {LINES} lines over {SECONDS} s, "
          f"~{N_PROC * LINES * 107 / 1e6:.1f} MB written\n")
    for s in schemes:
        if s == "dated_capped":
            # 30 KB per second-file and 100 KB of archives: proves the disk bound under a flood
            run(s, caps={"day_cap_mb": 30_000 / 2**20, "archive_cap_mb": 100_000 / 2**20})
        else:
            run(s)
