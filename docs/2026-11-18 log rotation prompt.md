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
