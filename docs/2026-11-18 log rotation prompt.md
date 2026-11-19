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

At this volume a month per file is enough: three streams give 36 archives a year, and a month of the busiest stream is ~5 MB. How fast a question across months is answered depends on the line format more than on the number of files: one JSON object per line (time with zone, level, logger, process, conversation, message, exception) lets DuckDB answer it in one SQL query over all the `.gz` files in the Mac mirror.

| | A. Monthly files, logrotate | B. Monthly files, app-managed | C. SQLite log database |
|---|---|---|---|
| Files a year | 36 archives, 3 live files | 36 | 1 database, plus the access text file |
| Analysis across months | DuckDB over `*.jsonl.gz`, one query | the same | SQL directly |
| Reading live | `tail -F`, with `jq` or lnav for JSON | through a symlink to the current month | a query script |
| Six writers | rename and reopen, 0 lines lost | no rename, 0 lines lost | SQLite locking, untested here |
| Code you own | ~40 lines (JSON formatter, flood guard, size fuse) and a 15-line logrotate conf | ~150 lines including compression and pruning, with tests | ~120 lines, a schema and a snapshot step |
| Host config | the logrotate conf, installed and dry-run checked by every deploy | the log directory only | none |
| fail2ban | new path | new path through a symlink, to be verified | keeps a text access log beside the database |
| Backup | rsync the directory | rsync the directory | snapshot with `VACUUM INTO`, then rsync |
| Your constraints | all met | all met | gives up the text files |

Every option also needs these parts:

- JSON lines for out and error. Access stays in uvicorn's text format, which the fail2ban filter already matches.
- A flood guard in the app that collapses repeated messages and caps each process's lines per minute, writing a count of what it dropped.
- A size fuse that stops a live file at 100 MB (out), 50 MB (access) or 20 MB (error) in a month.
- No stdout handler on production loggers, and supervisord's capture capped at 10 MB with 5 backups.
- loguru routed into the standard logging handlers, and the `error_file` handler set to WARNING.
- The files in `/var/log/fastapi_app/`, owned by chaehan.

Recommended: A. The app side stays standard library apart from ~40 lines, logrotate already runs daily on Ubuntu 24.04, and `dateyesterday` with `dateformat -%Y-%m` names each archive by the month it holds (`out-2026-11.jsonl.gz`). The deploy installs the conf and fails on a dry-run error, so it cannot vanish again unnoticed. B fits better if you want no host file at all and accept owning the rotation code. C fits if your analysis is mostly ad-hoc SQL on the VM and you drop the text-file constraint.
