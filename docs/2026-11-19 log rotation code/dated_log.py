"""Multi-process-safe file logging: one file per stream per day, named by the record's date.

Every process appends to <dir>/<YYYY-MM-DD>.<stream>.log with O_APPEND, one write(2) per
record. Nothing is ever renamed or truncated, so any number of processes (uvicorn master,
workers, bot subprocesses) share a directory without coordinating. A later step compresses
closed days and prunes old ones under an flock, so only one process does it at a time.

Disk bound per stream: archive_cap_mb + 2 * day_cap_mb (today's file plus yesterday's
until it is compressed).
"""
import fcntl
import gzip
import logging
import os
import shutil
import threading
import time
from pathlib import Path


class DatedFileHandler(logging.Handler):
    def __init__(self, directory, stream, day_cap_mb=50, keep_days=365, archive_cap_mb=300,
                 housekeeping=False, grace_s=120, datefmt="%Y-%m-%d"):
        super().__init__()
        self.dir = Path(directory)
        self.stream = stream
        self.day_cap = int(day_cap_mb * 2**20)
        self.keep_days = keep_days
        self.archive_cap = int(archive_cap_mb * 2**20)
        self.housekeeping = housekeeping
        self.grace_s = grace_s
        self.datefmt = datefmt          # tests pass "%Y-%m-%d_%H-%M-%S" for one file per second
        self.suffix = f".{stream}.log"
        self.key = None
        self.fd = None
        self.dropped = 0
        self.dir.mkdir(parents=True, exist_ok=True)

    def path(self, key):
        return self.dir / f"{key}{self.suffix}"

    def emit(self, record):
        try:
            key = time.strftime(self.datefmt, time.localtime(record.created))
            if self.key is None or key > self.key:      # never step back to an older day
                self._switch(key)
            data = (self.format(record) + "\n").encode("utf-8", "backslashreplace")
            if os.fstat(self.fd).st_size + len(data) > self.day_cap:
                if not self.dropped:
                    os.write(self.fd, f"[pid {os.getpid()}] day cap of {self.day_cap} bytes "
                                      f"reached; dropping records until the next day\n".encode())
                self.dropped += 1
                return
            os.write(self.fd, data)                      # O_APPEND: one atomic append per record
        except Exception:
            self.handleError(record)

    def _switch(self, key):
        old_key, dropped = self.key, self.dropped
        if self.fd is not None:
            os.close(self.fd)
        self.fd = os.open(self.path(key), os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o640)
        self.key, self.dropped = key, 0
        if dropped:
            os.write(self.fd, f"[pid {os.getpid()}] dropped {dropped} records on {old_key} "
                              f"after the day cap\n".encode())
        self._point_link(key)
        if self.housekeeping:
            timer = threading.Timer(self.grace_s, self.tidy)
            timer.daemon = True
            timer.start()

    def _point_link(self, key):
        """Keep <stream>.log pointing at the newest day, for fail2ban, tail -F and scripts."""
        link = self.dir / f"{self.stream}.log"
        try:
            if os.readlink(link) >= self.path(key).name:
                return
        except OSError:
            pass
        tmp = self.dir / f".{self.stream}.log.{os.getpid()}"
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        os.symlink(self.path(key).name, tmp)
        os.replace(tmp, link)                            # atomic: readers never see no link

    def tidy(self):
        """Compress closed days, then prune by age and by total size. One process at a time."""
        with open(self.dir / f".tidy{self.suffix}.lock", "w") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return
            now = time.time()
            today = time.strftime(self.datefmt, time.localtime(now))
            for raw in sorted(self.dir.glob(f"*{self.suffix}")):
                key = raw.name[: -len(self.suffix)]
                if raw.is_symlink() or key >= today or now - raw.stat().st_mtime < self.grace_s:
                    continue
                part = raw.with_name(f".{raw.name}.gz.part")   # hidden, so backups skip it
                with open(raw, "rb") as src, gzip.open(part, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                os.replace(part, raw.with_name(raw.name + ".gz"))
                os.unlink(raw)
            cutoff = time.strftime(self.datefmt, time.localtime(now - self.keep_days * 86400))
            archives = sorted(self.dir.glob(f"*{self.suffix}.gz"))
            total = sum(a.stat().st_size for a in archives)
            for a in archives:                           # oldest first
                if a.name[: len(cutoff)] >= cutoff and total <= self.archive_cap:
                    break
                total -= a.stat().st_size
                a.unlink()

    def close(self):
        self.acquire()
        try:
            if self.fd is not None:
                os.close(self.fd)
                self.fd = None
        finally:
            self.release()
        super().close()
