# Prompt: pick the right log rotation scheme for a single-VM Python service

Hand this to a model that knows Python logging and Linux log management. The question at the end is the one I need answered; everything above it is context it may not assume away.

## The deployment

One GCP VM (`n2-standard-2` Spot, Ubuntu 24.04, 11 GB disk, 7.1 GB used). It serves a FastAPI app under uvicorn behind nginx. supervisord runs the entry script:

```
exec uvicorn app_fastapi:app --host 0.0.0.0 --port 8080 \
     --workers $(( 2 * $(nproc) + 1 )) --log-level info \
     --log-config config/logging_config.json
```

So **five uvicorn worker processes** share one log path. The app also spawns a **Pipecat bot subprocess per conversation** (`main.py`), which configures logging separately with the same file names and runs for minutes at a time.

## Current logging configuration

`config/logging_config.json` is passed to uvicorn as `--log-config`, and `config/logging_config.py` holds equivalent dicts used by the subprocess. Handlers:

| Handler | Class | File | maxBytes | backupCount |
|---|---|---|---|---|
| `default` | `StreamHandler` (stdout) | — | — | — |
| `out_file` | `RotatingFileHandler` | `/var/log/fastapi_app.out.log` | 52,428,800 | 5 |
| `error_file` | `RotatingFileHandler` | `/var/log/fastapi_app.error.log` | 10,485,760 | 5 |
| `access_file` | `RotatingFileHandler` | `/var/log/fastapi_app.access.log` | 10,485,760 | 5 |

Loggers: root → `default` + `out_file`; `uvicorn` and `uvicorn.error` → `default` + `out_file` + `error_file` at WARNING; `uvicorn.access` → `default` + `access_file`; `fastapi` → `default` + `out_file` + `error_file` at INFO. `disable_existing_loggers` is false.

supervisord additionally captures the process stdout into `/var/log/supervisor/fastapi_app.out.log` and stderr into `fastapi_app.error.log`, with no rotation configured there.

## Measured state (2026-11-18)

| File | Bytes |
|---|---|
| `/var/log/fastapi_app.out.log` | 24,659,908 |
| `/var/log/fastapi_app.access.log` | 10,342,204 |
| `/var/log/fastapi_app.error.log` | 1,338,785 |
| `/var/log/supervisor/fastapi_app.out.log` | 44,871,485 |
| `/var/log/supervisor/fastapi_app.error.log` | 24,200,009 |

Every line exists twice, once from the app's `out_file` handler and once from supervisord capturing stdout.

## Why the current scheme exists

Commit `5906e8e` (2026-05-23): *"Replace unbounded FileHandler with RotatingFileHandler, reduce PROD log levels from DEBUG to INFO/WARNING (disk filled 1.1GB in 20 days)"*. Before that the files were rotated by **logrotate** on the host, producing `/var/log/fastapi_app.access.log-2026-05-01` style names with gzip. That logrotate config lived in `/etc/logrotate.d` and disappeared at some point, which is part of the problem: it was outside the repository and outside any test.

## Problems observed since

1. **Names carry no date.** `.1`–`.5` say nothing about when the contents were written, so nobody can open "last Tuesday". A backup alias that rsyncs `/var/log/fastapi_app.*.log*` to a Mac silently missed five rotations (14 MB) for six months because the mirror's newest date-named file looked like normal history rather than a gap.
2. **The bound is bytes, not time.** Five files of 50 MB is a window that shrinks as traffic grows; a busy week can erase a month of context.
3. **Multi-process rotation is unsafe.** Five uvicorn workers plus an unknown number of bot subprocesses each hold their own `RotatingFileHandler` on the same path. When one rotates, the others keep writing to the renamed inode, so lines land in the wrong file, the live file can be recreated more than once, and a rotation can delete a file another process still has open.
4. **No compression.** Text logs at these volumes compress roughly 8-10x; nothing is gzipped.
5. **Two copies of everything** (app handler + supervisord capture).
6. **Discovery is manual.** Finding yesterday's errors means opening a 24 MB file.

## Constraints I will not relax

- The **app keeps writing its own log files**. Do not propose "log to stdout only and let the supervisor own the file"; that approach was rejected. Whatever you propose must keep the app's own `out`/`error`/`access` files as first-class artifacts with the app as a writer.
- Configuration must live **in the repository**, reviewed like code, and survive a rebuild of the machine — no host-only files that can silently vanish.
- No log lines may be lost or duplicated at rotation, including while a bot subprocess is mid-conversation.
- Rotation must not require a process restart and must not depend on someone remembering a cron entry.
- The backup path (`rsync` from a Mac, run a few times a day) must keep working, and its pattern must be derivable from the naming scheme rather than guessed.
- Access logs must stay separable from application logs.

## What I want from you

1. A recommendation of the **best practice for multi-process Python logging into files on a single VM** in 2026, with the reason it wins. Compare at least: `TimedRotatingFileHandler` (with a custom `namer`/`rotator` for gzip), `WatchedFileHandler` plus external logrotate with `copytruncate`, a `QueueHandler`/`QueueListener` with one writer process, and an external collector (journald, Vector, Fluent Bit). Say which of these is safe with five writers and which only looks safe.
2. If the answer involves logrotate, give the exact `/etc/logrotate.d` file, how it is delivered and tested from the repository, and how `copytruncate` is made safe against five open file descriptors.
3. If the answer involves Python-side rotation, show how date-bearing filenames and gzip are produced, how N processes cooperate without races, and what the hard bound on disk is.
4. In either case: how do the app's own files and the supervisor's duplicates coexist without storing every line twice, given the constraint above?
5. A naming scheme that sorts by date and can be globbed by an rsync backup in one pattern, with the exact pattern for the Mac side.
6. A short "definition of done" a reviewer can test: a script or set of commands proving no line loss across a rotation, the disk bound holding, an old day being readable, and the backup picking up every file.
7. Any trap you would expect us to hit that is not in the list above.

## Findings, 2026-11-19

Six processes wrote 4000 numbered lines each, with a rotation every 0.5 to 1 s standing in for the daily one (Python 3.12.12, macOS):

| Scheme | Lines lost, two runs | Why |
|---|---|---|
| `RotatingFileHandler` (today) | 11%, 43% | each process rolls over when its own descriptor passes `maxBytes`, so one rotation shifts the backups once per process |
| `TimedRotatingFileHandler` with gzip | 77%, 80% | in 3.12 the second process to reach the boundary finds the archive, returns early and keeps writing into it after the gzip rotator has deleted it |
| logrotate `copytruncate` | 3 and 7 lines | lines written between the copy and the truncate are lost |
| logrotate `create` with `WatchedFileHandler` | 0, 0 | the rename keeps the inode and each process reopens the path before its next write |
| a file per period, never renamed | 0, 0 | nothing is renamed or truncated while open |

What any plan has to handle:

- Volume is ~212 KB a day (out ~41 KB, access ~164 KB, error ~7 KB), ~78 MB a year raw and ~10 MB compressed, read from the dates on the lines in the Mac mirror. The disk only overflows in a flood.
- The cascade is in the data: `fastapi_app.access.log.1` to `.4` on the Mac all hold lines from 2026-09-17 to 09-22. The Mac never builds up history because numbered names are reused and every `logsync` overwrites them.
- The uvicorn master loads `--log-config` as well (`uvicorn/config.py:274`), so six uvicorn processes hold the handlers.
- The bot's loguru sink (`config/logging_config.py:507`) writes straight into out.log with no rotation and no timestamp; ~23% of out.log's bytes start without a date.
- `--log-level info` overrides the JSON's WARNING for `uvicorn.error`, which put 1735 INFO lines into error.log.
- The 2026-05-22 rescue doc told you to remove the logrotate config. The stale `src/config/logrotate.conf` (monthly, restarts the app) was never installed.
- supervisord rotates its capture by default at 50 MB with 10 backups. The repository's conf sets `redirect_stderr=true`, so the 24 MB supervisor error.log comes from a different conf or is left over.
- fail2ban reads `/var/log/fastapi_app.access.log` with `backend = polling` and expands a glob only at start. Its jail and filter exist only on the host.
- `run_chatbot` (`app_fastapi.py:424`) logs the bot's stdout a second time in the worker.
- out.log measured 24.66 MB on the VM and 7.36 MB in the Mac copy synced 2026-11-18 23:07.

## Options, 2026-11-19 (your decision is open)

Speed decides nothing at this volume. On a synthetic year of the access log (600000 lines, 47 MB, 7.7 MB compressed), counting a month of 404s took 22 ms with grep, 44 ms with zgrep and 13 ms in SQLite with a time index, and writing one line into SQLite cost 8 µs. The number of files follows logrotate's period: yearly rotation gives each stream one live file and one archive a year.

| | A. Text files + logrotate, yearly | B. systemd journal | C. SQLite database |
|---|---|---|---|
| Files you handle | + 3 live files, 3 archives a year | + none; `journalctl` shows one stream | + 1 database, plus a text access log for fail2ban |
| Questions across months | + grep or zgrep over at most 2 files per stream | + indexed by time and field (`--since`, `-p warning`) | + SQL |
| Reading live | + `tail -F`, `less`, every text tool | + `journalctl -f` | − needs a polling query |
| Overflow | + `maxsize` fuse, checked daily; − a flood writes up to a day before the check | + cap and retention built in; − the cap is shared with system logs | − cap and pruning are yours to write |
| Six writers | + rename, then each process reopens: 0 lines lost in the test | + journald is the only writer | + SQLite's lock orders the writers |
| Code you own | + standard library handler, a 15-line config | − fields beyond level and tag need an extra package | − ~120 lines, schema, pruning, backup snapshot |
| Host config | − logrotate config, installed and dry-run checked by the deploy | − a journald drop-in for the cap | + none |
| Backup to the Mac | + rsync; an archive's name never changes | − binary, and macOS has no `journalctl`, so the VM must export text daily | − snapshot first, since a copy of a live database can be torn |
| fail2ban | + new path only | + native (`backend = systemd`) | − still reads the text access log |
| Your constraints | + all met | − the app no longer writes its own files | − the text files go |
| Standard practice | + the classic Unix setup, which nginx on your VM already uses | + Ubuntu's journal since 15.04 | − unusual for application logs |

Recommended: A. It meets every constraint with the tools Ubuntu already runs for nginx, the app side stays the standard library's `WatchedFileHandler`, and each file holds one year of one stream. The deploy installs the config from the repository and fails when `logrotate -d` reports an error:

```
/var/log/fastapi_app/out.log
/var/log/fastapi_app/error.log
/var/log/fastapi_app/access.log {
    su chaehan adm
    yearly
    maxsize 200M
    rotate 5
    dateext
    dateyesterday
    dateformat -%Y-%m-%d
    extension .log
    compress
    delaycompress
    create 0640 chaehan adm
    missingok
    notifempty
}
```

The three paths are named one by one, because a `*.log` glob would also match last year's archive while `delaycompress` keeps it uncompressed. An archive is named for the last day it holds: `access-2026-12-31.log.gz` is 2026, and a flood that passes 200 MB adds one archive named for its day. B is the cleaner design if you drop the own-files constraint, at the cost of the Mac backup. C offers nothing your volume needs.

Whichever you choose:

- No stdout handler on production loggers, and supervisord's capture capped at 10 MB with 5 backups.
- loguru routed into the standard logging handlers, and the `error_file` handler set to WARNING.
- Level, logger and process added to the out and error line format, so grep can filter by them. JSON lines pay off only once you query fields every week.
- Optional: a guard in the app that collapses a repeated message into one line with a count, which closes A's one-day flood window.
