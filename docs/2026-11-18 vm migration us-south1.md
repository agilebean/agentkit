# VM migration us-west1-a → us-south1-a, run as a test-first delivery

State: Story 1 done (2026-11-18). Next: Story 2, the Dallas capacity spike.
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

- [ ] T2.1 Given zone `us-south1-a`, when a Spot `n2-standard-2` is created, then it reaches `RUNNING` within 120s.
- [ ] T2.2 Given T2.1 fails with `ZONE_RESOURCE_POOL_EXHAUSTED`, when the same is tried in `us-south1-b` then `us-south1-c`, then a zone that reaches `RUNNING` is recorded and used for Story 4.
- [ ] T2.3 Given all three zones fail, then the migration stops here and the cost of a standard-priced instance is not paid.
- [ ] T2.4 Given the test instance is deleted, when `gcloud compute instances list` runs, then only `vm` in us-west1 exists and no orphan disk remains.

## Story 3 — image the running system with minutes of downtime, not hours

As the operator I want a consistent image of the live disk so that the new VM starts as a byte-for-byte copy (nginx sites, both certs, miniforge envs, supervisor config, git checkout).

- [ ] T3.1 Given `vm` is stopped, when `gcloud compute images create vm-cutover-20261118` runs, then the image reaches `READY` and its size is ≤ 13 GB.
- [ ] T3.2 Given the image is READY, when `vm` is started again, then `https://my.virtualfriend.chat/health` returns 200 within 5 minutes.
- [ ] T3.3 Given the stop and start, then the measured outage is under 6 minutes and the actual duration is written into the Test log.

## Story 4 — build the Dallas VM and prove it before DNS moves

As the operator I want a verified replacement serving both hostnames so that the DNS flip is a formality rather than the first test.

- [ ] T4.1 Given the image, when `vm` is created in the Story 2 zone with `--provisioning-model=SPOT --instance-termination-action=STOP --maintenance-policy=TERMINATE --no-restart-on-failure --no-boot-disk-auto-delete`, then `scheduling.provisioningModel` reads `SPOT` and the instance holds the new static address.
- [ ] T4.2 Given the new address, when `curl http://<new>:8080/health` runs, then the body carries `"status":"ok"` or `"status":"healthy"`.
- [ ] T4.3 Given the new address, when `supervisorctl status` runs over SSH, then `fastapi_app` is `RUNNING`.
- [ ] T4.4 Given `openssl s_client -servername my.virtualfriend.chat` and `-servername api.virtualfriend.chat` against the new address, then both return the correct CN, a SAN matching the hostname, and an expiry at least 60 days out.
- [ ] T4.5 Given a hosts-file override pointing both hostnames at the new address, when a real chatbot session is started and `/health` plus `/account` are requested, then the session starts and both respond 200.
- [ ] T4.6 Given the old VM is still running on the old address, when the same hostname is resolved without the override, then it still reaches the old VM — proving the two environments are independent until the flip.
- [x] T4.7 Given all 34 pages in `virtualfriend-pages/sitemap.xml`, when each is fetched and grepped for `34.145.45.178`, `35.224.243.25` and `:8080`, then no page contains any of them, so no Dorik page needs editing when the address changes.

## Story 5 — flip both DNS records and prove every path that carries the address

As the operator I want DNS and the deploy pipeline on the new machine so that a `git push` still reaches production.

- [ ] T5.1 Given the two A records, when Chaehan replaces the data field in both, then `dig +short my.virtualfriend.chat` and `dig +short api.virtualfriend.chat` both return the new address within 10 minutes.
- [ ] T5.2 Given propagation, when `https://my.virtualfriend.chat/health` and `https://api.virtualfriend.chat/health` are requested, then both return 200 from the new VM (confirmed by the access log on the new host, not just the status code).
- [ ] T5.3 Given `SSH_HOST` is updated to the new address, when `gh workflow run deploy.yml` runs, then the run is green and its log shows the new host.
- [ ] T5.4 Given the workflow, when a no-op commit is pushed, then `git log -1` on the new VM shows that commit within 2 minutes — the auto-deploy path is proven end to end, not inferred.
- [ ] T5.5 Given DNS is flipped, when the old VM is still running, then requests to the old address still answer, so the rollback window is real.

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

- [ ] T8.1 Given 7 quiet days, when the old instance, disk, image and `ip-virtualfriend` are deleted, then `gcloud compute instances list`, `disks list`, `images list` and `addresses list` show no us-west1 leftovers.
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
