# Log rotation for virtualfriend: the answer

Answers [the prompt of 2026-11-18](2026-11-18%20log%20rotation%20prompt.md). The handler, its tests and the comparison script are in [2026-11-19 log rotation code](2026-11-19%20log%20rotation%20code/).

Have every process append to a file named for the day its line was written, such as `/var/log/fastapi_app/2026-11-19.out.log`, and never rename a file that a process may still hold open. With six processes writing at once, this lost 0 of 24000 lines in each of two runs; the current `RotatingFileHandler` lost 11% and 43%.

Your Mac mirror already shows the damage. `fastapi_app.access.log.1` to `.4` all hold lines from the same five days, 2026-09-17 to 09-22: six uvicorn processes each rotate on their own, so one rotation pushes the backups down up to six times and the five backups hold ~1 real generation. The Mac lost history for a second reason: numbered names are reused, so every `logsync` overwrites the local `.1` with the server's new `.1`. A day's name is never reused, so the same rsync accumulates every day.

The disk bound is hard: 690 MB for the three streams at the caps below, against ~212 KB written on a normal day and 3.9 GB free. Everything lives in the repository as Python and JSON; the deploy only creates one directory.

What would change this is fail2ban. It reads the access log by path, so the design keeps `access.log` as a symlink to today's file, and fail2ban's polling backend should treat the switch at midnight as a rotation. If the check after the first midnight shows it does not, the runner-up wins: logrotate with `create` plus `WatchedFileHandler`, which also lost no lines but names files by rotation date and cannot cut a file early during a flood.

One choice is yours. Under a flood, a hard bound means the handler stops writing a stream for the rest of the day once its day cap is reached, leaving one marker line and the count of dropped records. The caps below sit ~300 to ~2800 times above a normal day. Dropping the cap drops the bound, and an uncapped file is what filled the disk in May.

## 1. Which scheme is safe with six writers

The test: six processes write 4000 numbered lines each over 5 s, with a rotation every 0.5 to 1 s standing in for the daily one, on Python 3.12.12 and macOS. `compare_handlers.py` reruns it. On the VM's ext4 disk, `O_APPEND` gives the same guarantee.

| Scheme | Lost, two runs | Six writers | Why |
|---|---|---|---|
| `RotatingFileHandler` (today) | 11%, 43% | unsafe | Each process rolls over when its own descriptor passes `maxBytes`. After one process renames the file, the others still point at the full renamed file, so each rolls over again and pushes the backups down once more. |
| `TimedRotatingFileHandler` with gzip `namer` and `rotator` | 77%, 80% | unsafe | In 3.12, `doRollover` returns early when the dated file exists, without reopening and without moving the next rollover time. Processes 2 to 6 keep writing into the archive until they restart, and a gzip rotator has already deleted that archive. Older CPython releases deleted the first process's archive instead. |
| `WatchedFileHandler` with logrotate `copytruncate` | 3 and 7 lines | looks safe | Lines written between the copy and the truncate are lost. No setting closes that window, with one writer or six. |
| `WatchedFileHandler` with logrotate `create` and `delaycompress` | 0, 0 | safe | A rename keeps the inode, and each process checks the path before every write and reopens. A line that races the rename lands in the renamed file, which stays uncompressed for one cycle. |
| `QueueHandler` and `QueueListener` with one writer | not run | threads only | The queue lives inside one process. Sharing it needs a common parent, but uvicorn starts its own workers and each bot starts through `conda run python main.py`. What remains is a socket log server: one more process to supervise, and lines are dropped while it is down. |
| Collector (journald, Vector, Fluent Bit) | not run | safe, excluded | journald and Vector's file sink become the writer of the files, which your first constraint rules out. Tailing the app's files leaves the rotation to someone else. It adds a daemon and host config for ~212 KB a day. |
| Dated files, no rename (recommended) | 0, 0 | safe | Nothing is renamed or truncated while open, so nothing can race. A closed day is compressed 120 s after the switch by the one process holding a lock. |

Java's logback reached the same rule for several JVMs writing one rolling log: its prudent mode forbids a fixed active file name, because most operating systems refuse to rename a file another process has open ([manual](https://logback.qos.ch/manual/appenders-rolling.html)).

## 2. logrotate

The recommendation does not use logrotate. `copytruncate` cannot be made safe against open descriptors: it lost 3 and 7 lines in the test above. If you ever fall back to logrotate, the safe pairing is `create` with `WatchedFileHandler` and `delaycompress`. It still cannot name a file by its own date and also rotate early on a busy day: the early rotation's dated name collides with that day's file, logrotate skips the rotation, and the file keeps growing.

The old config did not vanish by accident. `src/docs/rescues/2026-05-22-logging-fix-prompt.md` tells you to `sudo rm` both `/etc/logrotate.d` files once `RotatingFileHandler` is deployed. `src/config/logrotate.conf` (monthly, with `supervisorctl restart` in `postrotate`) is still in the repository and was never installed by the deploy; delete it with this change so nobody installs it later.

## 3. The Python side

`DatedFileHandler` in [dated_log.py](2026-11-19%20log%20rotation%20code/dated_log.py) works like this.

- Each record goes to `<directory>/<date>.<stream>.log`, the date taken from the record's creation time, so a line from 23:59:59.9 lands in its own day. A process only moves forward to a newer day.
- The file is opened with `O_APPEND` and each record goes out in one `os.write`, so lines from different processes never overwrite or split each other.
- 120 s after a uvicorn process moves to a new day, it tries an `flock`. The one that gets it compresses each closed day into a hidden `.part` file, renames that to `.gz` and deletes the raw file, then deletes archives older than 365 days and, oldest first, any beyond the archive cap. A bot may exit before its timer fires, so only the uvicorn config turns housekeeping on.
- `<stream>.log` stays a symlink to the newest day, for fail2ban, `tail -F` and `scripts/extractip.sh`.

The wiring in `config/logging_config.json`, with the same keys in both production dicts of `logging_config.py` and `"housekeeping": false` in the subprocess one:

```json
"out_file": {
    "class": "config.dated_log.DatedFileHandler",
    "formatter": "default",
    "directory": "/var/log/fastapi_app",
    "stream": "out",
    "day_cap_mb": 100,
    "archive_cap_mb": 200,
    "keep_days": 365,
    "housekeeping": true
}
```

uvicorn puts `--app-dir` (default `.`) on `sys.path` before it loads the log config (`uvicorn/main.py:514` in 0.34.0), so `config.dated_log` imports from `~/virtualfriend/src` in the master and in each worker.

The bot's loguru sink must stop opening the file itself. The production branch of `setup_ttfb_metrics_logging()` becomes:

```python
class _ToStdlib(logging.Handler):
    def emit(self, record):
        logging.getLogger(record.name).handle(record)

loguru_logger.add(_ToStdlib(), format="pipecat: {message}",
                  level=os.getenv("PIPECAT_LOG_LEVEL", "INFO"))
```

Pipecat lines then pass through the same handler and get the same timestamp as every other line.

Per stream, the bound is the archive cap plus two day caps: today's file, and yesterday's until it is compressed shortly after midnight.

| Stream | Normal day | Day cap | Archive cap | Bound |
|---|---|---|---|---|
| out | ~41 KB | 100 MB | 200 MB | 400 MB |
| access | ~164 KB | 50 MB | 100 MB | 200 MB |
| error | ~7 KB | 20 MB | 50 MB | 90 MB |
| total | ~212 KB | | | 690 MB |

At normal volume a year of compressed days takes ~10 MB, so the 365-day window decides what is kept and the caps only act in a flood. The normal days come from the dates on the mirrored lines: out.log holds 7.36 MB from 2026-05-23 to 11-18, access.log 10.34 MB from 2026-09-17 to 11-18. The prompt measured out.log at 24.66 MB on the VM, while the Mac copy synced 2026-11-18 23:07 holds 7.36 MB, so run `wc -c` on both before you trust the out cap.

## 4. App files and the supervisor's copies

Every production logger sends each line to the `default` stdout handler as well as to its file, and supervisord stores stdout a second time. Remove `default` from every logger in the JSON and in both production dicts. Afterwards stdout receives only what never passes through logging: `print()`, a traceback from before logging is configured, output from native libraries such as Daily's. That is what supervisord's file is good for, a record of the crashes the app could not log itself, while the app's files stay the one full record.

supervisord already rotates its capture: without settings it keeps 50 MB plus 10 backups per stream. Set the size explicitly in `src/config/fastapi_app.conf`; its rotation is safe because supervisord is that file's only writer.

```ini
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=5
```

The repository's conf has `redirect_stderr=true`, so nothing should be writing `/var/log/supervisor/fastapi_app.error.log` (24 MB). Either the VM's conf differs from the repository's or the file is a leftover; `diff` the two before deleting it. The same holds for every host file this design touches: the deploy should install the supervisor conf and the fail2ban jail from the repository and fail when an installed copy differs, so a host file can no longer vanish or drift without anyone noticing.

## 5. Names and the backup

```
/var/log/fastapi_app/              owned by chaehan, created by the deploy
  2026-11-18.access.log.gz         a closed day, compressed
  2026-11-18.error.log.gz
  2026-11-18.out.log.gz
  2026-11-19.access.log            today, live
  2026-11-19.error.log
  2026-11-19.out.log
  access.log -> 2026-11-19.access.log
  error.log  -> 2026-11-19.error.log
  out.log    -> 2026-11-19.out.log
```

`ls` lists the days in order with a day's three streams together, and `zcat 2026-11-17.error.log.gz` opens last Tuesday's errors. The one pattern is `20??-??-??*.log*`: it takes every dated file, raw or compressed, and leaves out the symlinks and the hidden `.part` files. On the Mac, this replaces `logsync` in `src/scripts/bash_aliases.local` and `~/.bash_aliases`:

```bash
alias logsync="cd \"$HOME/Software/virtualfriend/src/logs/fastapi_app/\" && \
$(which rsync) -av --include='20??-??-??*.log*' --exclude='*' \
  -e \"ssh -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=2 -i ~/.ssh/google_compute_engine\" \
  chaehan@34.174.158.148:/var/log/fastapi_app/ ./ && \
for gz in 20??-??-??*.log.gz; do rm -f \"\${gz%.gz}\"; done"
```

A sync during the day copies today's raw file; the loop deletes that copy once the day's `.gz`, the complete version, has arrived. The command leaves out `--delete`, so the Mac keeps every day while the VM drops days after 365. The new folder `src/logs/fastapi_app/` starts clean, and `src/logs/fastapi/` keeps the old names as history.

## 6. Definition of done

`python -m pytest -q test_dated_log.py` in the code folder runs five tests with six processes rotating every second. They passed here in 13.7 s.

| Test | Proves |
|---|---|
| `test_no_line_lost_duplicated_or_misfiled` | all 18000 lines are present once, each in the file of its own second |
| `test_closed_periods_are_compressed_and_readable` | every closed period is a valid `.gz` whose first line parses |
| `test_link_points_at_newest_period` | `out.log` points at the newest file |
| `test_disk_bound_holds_under_a_flood` | ~1.9 MB written against a 30 KB day cap and a 100 KB archive cap never exceeds the bound |
| `test_backup_pattern_picks_up_every_dated_file` | the rsync pattern copies exactly the dated files, run with macOS's own rsync |

Add one test with the change: the handler sections of `logging_config.json` and `LOGGING_CONFIG_PROD` must agree, since the two files duplicate each other today.

On the VM after the deploy, and again the morning after the first midnight:

```bash
ls -l /var/log/fastapi_app/                       # dated files; yesterday is .gz after 00:02
readlink /var/log/fastapi_app/access.log          # today's file
du -sh /var/log/fastapi_app/                      # under 690 MB
zcat /var/log/fastapi_app/$(date -d yesterday +%F).error.log.gz | head -3
sudo lsof +L1 | grep fastapi_app                  # deleted files still held open: yesterday's at most
sudo fail2ban-regex /var/log/fastapi_app/access.log /etc/fail2ban/filter.d/fastapi.conf
sudo fail2ban-client status fastapi_app           # "Total failed" must keep rising after midnight
```

On the Mac, run `logsync`; then this prints nothing when every dated file has arrived:

```bash
comm -13 <(ls ~/Software/virtualfriend/src/logs/fastapi_app | sort) <(ssh -i ~/.ssh/google_compute_engine chaehan@34.174.158.148 'ls /var/log/fastapi_app | grep "^20"' | sort)
```

## 7. Traps not in your list

1. The uvicorn master is a sixth writer. It loads `--log-config` too (`uvicorn/config.py:274`, then each worker again at `_subprocess.py:76`), so it holds the three handlers like any worker.
2. The bot writes the file a second way. `setup_ttfb_metrics_logging()` points loguru straight at `/var/log/fastapi_app.out.log` (`config/logging_config.py:507`) with no rotation, so it follows renamed files and can write into deleted ones. Its lines have no timestamp (`pipecat: {message}`), and ~23% of the mirrored out.log bytes start without a date, tracebacks and JSON dumps included, so no split by time can place them. The loguru change in section 3 fixes both.
3. `--log-level info` in `start_fastapi_app.sh` overrides the JSON's WARNING for `uvicorn.error`, because uvicorn sets that logger's level after loading the config. The mirrored error.log holds 1735 INFO lines such as "Child process [1114] died". Put `"level": "WARNING"` on the `error_file` handler itself.
4. Creating or renaming a file in `/var/log` needs write permission on that directory. If chaehan lacks it, `RotatingFileHandler` fails its rollover on every record from then on and the lines go to stderr as "--- Logging error ---". `namei -l /var/log/fastapi_app.out.log` shows the permissions; the new directory belongs to chaehan, which removes the question.
5. fail2ban's jail and filter are host-only files, the same kind as the logrotate config that disappeared. Its `logpath` must move to `/var/log/fastapi_app/access.log`, never to a glob: fail2ban expands globs only at start and would stop banning after the first midnight. Keep the access format as it is, since the filter matches `INFO:\s+<HOST>`.
6. A process that writes nothing after midnight keeps yesterday's raw file open after it is compressed and deleted, so `df` reports more than `du` until that process writes again. `lsof +L1` shows it, and it never exceeds one day.
7. File dates follow the VM's time zone, like the timestamps inside the lines. If the VM runs UTC, a Seoul Tuesday spans two files; `timedatectl` shows the zone.
8. `run_chatbot` (`app_fastapi.py:424`, behind the streaming endpoint at line 544) reads the bot's stdout and logs it again in the worker. Lines the bot sends to stdout, from its `uvicorn` and `fastapi` loggers and `print()`, are written once by the bot and once more by the worker. Once the bot's stdout handlers are gone, only `print()` output takes that path.
