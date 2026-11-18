# VM migration us-west1-a → us-south1-a, run as a test-first delivery

State: stories 1-3 done on 2026-11-18, image `vm-cutover-20261118` READY (12 GB, us). Next: choose image move or clean rebuild, then Story 4.
Resume: `restart vm migration` → run the *Resume checks* below, continue at the first unchecked acceptance test. `stop vm migration` → finish the current step, change nothing else, update *State*.

The instance is a Spot `n2-standard-2`: $41.40/month in Oregon against $15.34/month in Dallas, so $26.06/month and $313/year, plus $7.32/month already recovered by releasing an unattached address. Compute Engine total was $44.68/month, so the instance and RAM are effectively the whole line.

## Delivery rules

- Each story has acceptance tests written before the work, in Given/When/Then form. A story is done only when every test passes with evidence in the *Test log*; a failing test stops the next story.
- Nothing is deleted or released early: the old VM, its disk, its image and `34.145.45.178` all survive until Story 8, which is what keeps rollback a DNS edit.
- No standard-priced VM is ever created. Starting a stopped Spot VM stays Spot; if Dallas has no Spot capacity the restart logs an error and leaves the VM stopped.
- Chaehan touches only two Squarespace records. Everything in GCP, GitHub and the repo is agent work.

## Inventory as of 2026-11-18

| Item | Value |
|---|---|
| Instance | `vm`, `us-west1-a`, `n2-standard-2`, SPOT, termination action `STOP`, `automaticRestart=false` |
| Instance ID | `3228524999645469894` |
| Boot disk | `persistent-disk-0`, 12 GB, `autoDelete=false`, 69% full, Ubuntu 24.04 |
| Public addresses | `ip-virtualfriend` = `34.145.45.178`, us-west1, IN_USE by `vm` |
| DNS records on the VM | **A `my`** and **A `api`**, both `34.145.45.178` |
| Zone nameservers | `ns-cloud-c1..c4.googledomains.com` (Google-hosted zone, edited in the Squarespace panel) |
| TLS | two Let's Encrypt certs: CN/SAN `my.virtualfriend.chat` (to 2027-01-18) and CN/SAN `api.virtualfriend.chat`, both domain-bound so they survive the move |
| nginx | `sites-enabled`: `my.virtualfriend.chat`, `api.virtualfriend.chat`, `default`; all listen `0.0.0.0:80/443` |
| App | `supervisorctl`: `fastapi_app` RUNNING on 8080; `flask_app` was already FATAL before this work |
| Endpoints | `https://my.virtualfriend.chat/health` 200, `https://api.virtualfriend.chat/health` 200 (same app, production) |
| Deploy | `.github/workflows/deploy.yml`, `appleboy/ssh-action`, secret `SSH_HOST` = old IP, repo `agilebean/virtualfriend` |
| Preemption | sink `vm-preemption-sink` (filter on the instance ID above) → topic `vm-preemptions` → gen2 function `restart-vm-on-preemption`, us-central1, `ZONE=us-west1-a` |
| App URL | `FASTAPI_BASE_URL = https://my.virtualfriend.chat` in `config/constants.py`, no change needed |

## What crosses over, and what does not

State is small; the disk is not. The database is `test`: 3 collections, 112 `memories` documents, 1 `settings`, 0 `locks` — under 1 MB of data on a 7.2 GB used disk.

| Artifact | Size / count | How it crosses |
|---|---|---|
| MongoDB `test` DB | 0.7 MB, 112+1 docs | `mongodump` → `mongorestore` |
| `.env` | 60 keys, mode 664 today | copy over SSH, `chmod 600`, never committed |
| `src/config/virtualfriend-demo.json` | 2.3 KB, GCP **service-account key** | copy; used by `config/validation.py` |
| `src/config/gcloud_client_secret.json`, `client_secret_gmail.json` | 810 B, 408 B | copy |
| `~/.ssh/id_rsa` + `authorized_keys` | 3.4 KB | copy keys, regenerate host keys |
| certbot account + 2 certs | `/etc/letsencrypt` | reissue with certbot (HTTP-01) |
| fail2ban: `jail.d/fastapi_app.local`, `filter.d/fastapi.conf`, `/var/log/fastapi_app.access.log` | 5398 banned IPs | copy configs, recreate log path; bans restore from `/var/lib/fail2ban/fail2ban.sqlite3` (3.3 MB) — verified they survived a reboot |
| nginx: 3 sites, 2 LE certs | — | copy site configs |
| supervisor: `fastapi_app` | 1 unit | recreate; `flask_app` is dropped (already FATAL) |
| apt: 55 manual packages | — | `apt-mark showmanual` list → install |
| Python: 161 packages, 3.12.8 | `requirements.txt` 146 lines | rebuild env from today's `pip freeze` |
| nltk `tokenizers` | 64 MB | re-download |
| VM-only git files | `system_prompt_components.py`, `environment.yml`, `src/dump/`, `migrate_emotional_citations_vm.py` | copy or upstream first |
| Logs | app/chat/mongo synced locally; `/var/log` 286 MB | all synced down, only the last 30 days carried |
| Junk | 12 GB disk 69% full, 286 MB `/var/log`, dead `flask_app` | not carried |

Secrets decision: `.env` stays on the VM at mode `600`. Secret Manager was priced and rejected for now — 6 active versions free then $0.06 each, so 60 keys ≈ $3.24/month, and it does not defend against a compromised server, because the app's identity can read the same secrets. The real exposure is the service-account key in `src/config/`: it should be rotated and replaced by the VM's attached identity once `config/validation.py` no longer needs a key file.

## Where the Squarespace records are

Squarespace → **Domains** → `virtualfriend.chat` → **DNS settings**. The panel lists the zone's records in a table with an edit (pencil) control per row; custom records default to a 4-hour TTL, and the record editor carries the TTL field, which already holds the 5-minute value Chaehan set.

Two rows change, both type **A**, both data `34.145.45.178`:

| Host name | Type | Data before | Data after |
|---|---|---|---|
| `my` | A | `34.145.45.178` | new address |
| `api` | A | `34.145.45.178` | new address |

`www` is a CNAME to `virtualfriend.dcms.site` and the apex A record is `18.119.18.18` (Dorik) — neither changes, so the public marketing site is untouched by this work.

## Story 1 — stop paying for an address nothing uses ✔

As the operator I want an unattached static IP released so that the bill stops carrying $7.32/month for nothing.

- [x] T1.1 Given `virtualfriend-ip` shows status `RESERVED` and no users, when I delete it, then `gcloud compute addresses list` returns only `ip-virtualfriend` and no error.
- [x] T1.2 Given the address is gone, when `dig my` and `dig api` run, then both still return `34.145.45.178`.

Evidence: deleted 2026-11-18; `addresses list` now shows one address, `34.145.45.178`, IN_USE.

## Story 2 — prove Dallas has Spot capacity before touching production

As the operator I want a throwaway Spot launch in Dallas so that the migration cannot end in an unbootable instance.

- [x] T2.1 Given zone `us-south1-a`, when a Spot `n2-standard-2` is created, then it reaches `RUNNING` within 120s.
- [ ] T2.2 Given T2.1 fails with `ZONE_RESOURCE_POOL_EXHAUSTED`, when the same is tried in `us-south1-b` then `us-south1-c`, then a zone that reaches `RUNNING` is recorded and used for Story 4.
- [ ] T2.3 Given all three zones fail, then the migration stops here and the cost of a standard-priced instance is not paid.
- [x] T2.4 Given the test instance is deleted, when `gcloud compute instances list` runs, then only `vm` in us-west1 exists and no orphan disk remains.

## Story 3 — image the running system with minutes of downtime, not hours

As the operator I want a consistent image of the live disk so that the new VM starts as a byte-for-byte copy (nginx sites, both certs, miniforge envs, supervisor config, git checkout).

- [x] T3.1 Given `vm` is stopped, when `gcloud compute images create vm-cutover-20261118` runs, then the image reaches `READY` and its size is ≤ 13 GB.
- [x] T3.2 Given the image is READY, when `vm` is started again, then `https://my.virtualfriend.chat/health` returns 200 within 5 minutes.
- [x] T3.3 Given the stop and start, then the measured outage is under 6 minutes and the actual duration is written into the Test log.

## Story 4 — build the Dallas VM and prove it before DNS moves

As the operator I want a verified replacement serving both hostnames so that the DNS flip is a formality rather than the first test.

- [ ] T4.1 Given the image, when `vm` is created in the Story 2 zone with `--provisioning-model=SPOT --instance-termination-action=STOP --maintenance-policy=TERMINATE --no-restart-on-failure --no-boot-disk-auto-delete`, then `scheduling.provisioningModel` reads `SPOT` and the instance holds the new static address.
- [ ] T4.2 Given the new address, when `curl http://<new>:8080/health` runs, then the body carries `"status":"ok"` or `"status":"healthy"`.
- [ ] T4.3 Given the new address, when `supervisorctl status` runs over SSH, then `fastapi_app` is `RUNNING`.
- [ ] T4.4 Given `openssl s_client -servername my.virtualfriend.chat` and `-servername api.virtualfriend.chat` against the new address, then both return the correct CN, a SAN matching the hostname, and an expiry at least 60 days out.
- [ ] T4.5 Given a hosts-file override pointing both hostnames at the new address, when a real chatbot session is started and `/health` plus `/account` are requested, then the session starts and both respond 200.
- [ ] T4.6 Given the old VM is still running on the old address, when the same hostname is resolved without the override, then it still reaches the old VM — proving the two environments are independent until the flip.
- [x] T4.7 Given all 34 pages in `virtualfriend-pages/sitemap.xml`, when each is fetched and grepped for `34.145.45.178`, `35.224.243.25` and `:8080`, then no page contains any of them, so no Dorik page needs editing when the address changes.

## Story 4b — carry the bot defence, which is fail2ban and not a script

As the operator I want the bot blocking to arrive with the app so that the move does not reopen the door to 5398 banned addresses.

- [ ] T4b.1 Given the new VM, when `fail2ban-client status` runs, then both jails are active (`sshd` and `fastapi_app`).
- [ ] T4b.2 Given `jail.d/fastapi_app.local` points at `/var/log/fastapi_app.access.log`, when the app writes one 404 line from a probe IP, then `fail2ban-client status fastapi_app` shows `Total failed` incremented — the log path is wired, not just configured.
- [ ] T4b.3 Given the ban list exported from the old VM, when it is replayed on the new one, then `fail2ban-client banned` returns at least 5398 entries.
- [ ] T4b.4 Given `banaction = nftables`, when a banned address is checked, then the block is present in `nft list ruleset` and a request from it is refused.
- [ ] T4b.5 Given the old VM keeps serving until cutover, then the old and new ban lists are independent, so a mistake on the new VM cannot unlock the live one.

## Story 5 — flip both DNS records and prove every path that carries the address

As the operator I want DNS and the deploy pipeline on the new machine so that a `git push` still reaches production.

- [ ] T5.1 Given the two A records, when Chaehan replaces the data field in both, then `dig +short my.virtualfriend.chat` and `dig +short api.virtualfriend.chat` both return the new address within 10 minutes.
- [ ] T5.2 Given propagation, when `https://my.virtualfriend.chat/health` and `https://api.virtualfriend.chat/health` are requested, then both return 200 from the new VM (confirmed by the access log on the new host, not just the status code).
- [ ] T5.3 Given `SSH_HOST` is updated to the new address, when `gh workflow run deploy.yml` runs, then the run is green and its log shows the new host.
- [ ] T5.4 Given the workflow, when a no-op commit is pushed, then `git log -1` on the new VM shows that commit within 2 minutes — the auto-deploy path is proven end to end, not inferred.
- [ ] T5.5 Given DNS is flipped, when the old VM is still running, then requests to the old address still answer, so the rollback window is real.
- [ ] T5.6 Given T5.2 to T5.4 pass, when `vm-cutover-20261118` is deleted, then `images list` is empty and the old VM still boots from its own disk — the image is a safety net for the cutover window only, and its storage is not carried as a monthly cost.

## Story 6 — keep the preemption chain alive on the new instance

As the operator I want the restart function to follow the VM so that a Spot reclaim does not leave the product offline.

- [ ] T6.1 Given the sink filter currently matches instance ID `3228524999645469894`, when it is updated to `resource.labels.instance_name="vm"`, then `gcloud logging sinks describe` shows the new filter with the same destination and no writer-identity change.
- [ ] T6.2 Given `deploy.sh` has been read and confirmed to only set environment and rebuild, when it runs with `ZONE=us-south1-a`, then the function's `serviceConfig.environmentVariables.ZONE` reads `us-south1-a`.
- [ ] T6.3 Given `simulate-maintenance-event`, when the VM is reclaimed, then the function log records a restart attempt and the VM returns to `RUNNING` within 10 minutes.
- [ ] T6.4 Given the restart, when `scheduling.provisioningModel` is read, then it is still `SPOT` — no standard-priced instance appears in `instances list`.
- [ ] T6.5 Given spot capacity is exhausted (negative test, by reasoning and by reading the code path), then the function logs an error and leaves the VM stopped rather than creating a standard VM.

## Story 7 — make the repository tell the truth

As the operator I want no stale address in the codebase so that the next person reading it does not SSH into a deleted VM.

- [ ] T7.1 Given the change, when `grep -rn "34\.145\.45\.178"` runs over the repo, then the only hits are history (`logs/`, `_archive/`) or this document.
- [ ] T7.2 Given `scripts/datasync.sh`, `scripts/disk_usage_breakdown.sh`, `scripts/disk_cleanup.sh`, `docs/*` and the CLAUDE.md quick reference are updated, then `bash -n` passes on each script.
- [ ] T7.3 Given `gcloud config set compute/zone us-south1-a`, when the `gc` alias runs, then it opens a shell on the new VM.
- [ ] T7.4 Given the stale `Host vm.us-west1-a.virtualfriend-demo` block is removed from `~/.ssh/config`, when `ssh vm.us-south1-a.virtualfriend-demo` runs, then gcloud has regenerated a working entry.

## Story 8 — decommission on day 8, only if every earlier test held

As the operator I want the Oregon resources retired so that the saving actually lands.

- [ ] T8.1 Given 7 quiet days, when the old instance, its disk and `ip-virtualfriend` are deleted, then `gcloud compute instances list`, `disks list` and `addresses list` show no us-west1 leftovers.
- [ ] T8.2 Given the next billing cycle, when Billing → Reports is filtered to us-south1 for 30 days, then the compute line is ≈ $15-18 instead of $44.68.

Rollback, at any point before T8.1: start `vm` in `us-west1-a`, point both A records back to `34.145.45.178`, reset `SSH_HOST`, `gcloud config set compute/zone us-west1-a`. User data is in MongoDB and Stripe, so only local chat logs written after the image are affected.

## Resume checks

Run before continuing; they say which story is live without creating duplicates.

| Check | Reads | Means |
|---|---|---|
| `gcloud compute addresses list` | only `ip-virtualfriend`, IN_USE | Story 1 done |
| `gcloud compute images list --filter=name=vm-cutover-20261118` | empty or READY | Story 3 not started or done |
| `gcloud compute instances list` | `vm` in us-west1 only / also us-south1 | Story 4 not started or done |
| `dig +short my.virtualfriend.chat` | old vs new address | Story 5 pending or done |
| `gh secret list -R agilebean/virtualfriend` | `SSH_HOST` value | Story 5.3 pending or done |
| `gcloud logging sinks describe vm-preemption-sink` | ID filter vs name filter | Story 6 pending or done |
| `gcloud run services describe restart-vm-on-preemption --region=us-central1` | `ZONE` value | Story 6.2 pending or done |

Hard rules while this runs: never release `34.145.45.178` or delete the old disk before T8.1, never touch `patches/pipecat/*`, never create a standard-priced VM, and never flip DNS before T4.5 passes.

## Test log

| ID | Date | Result | Evidence |
|---|---|---|---|
| T1.1 | 2026-11-18 | pass | `virtualfriend-ip` (35.224.243.25) deleted; `addresses list` shows only `34.145.45.178` IN_USE |
| T1.2 | 2026-11-18 | pass | `dig my` and `dig api` both `34.145.45.178` after deletion |
| T4.7 | 2026-11-18 | pass | 34/34 sitemap pages fetched, 0 containing the old IP, the dead IP or `:8080`; no page fetch failed |
| T2.1 | 2026-11-18 | pass | `spot-probe` n2-standard-2 SPOT reached RUNNING in `us-south1-a` in 17s |
| T2.4 | 2026-11-18 | pass | probe deleted; `instances list` shows only `vm` in `us-west1-a` |
| T3.1 | 2026-11-18 | pass | image `vm-cutover-20261118` READY, 12 GB, storage location `us`, created 2026-11-18T03:32:23-08:00 |
| T3.2 | 2026-11-18 | pass | `/health` 200 on `34.145.45.178` at 203s after the stop began |
| T3.3 | 2026-11-18 | pass | stop 29s, image 133s, start 13s; 203s total downtime against a 6-minute budget |
| — | 2026-11-18 | pass | pre-cutover sync: 112 `memories` + 1 `settings` restored locally, 3 chat logs, nginx and fail2ban logs (8.3 MB), ban list 5398 IPs exports to `src/logs/vm-extra/fail2ban_banned.txt` |
