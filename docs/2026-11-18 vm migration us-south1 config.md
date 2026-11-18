# One-shot configuration: virtualfriend VM

Every value needed to build the production machine from nothing, in the order it is applied. The plan and its acceptance tests are in [2026-11-18 vm migration us-south1.md](2026-11-18%20vm%20migration%20us-south1.md).

Values marked ✔ were read off the running system on 2026-11-18, not copied from an older document.

## 1. Identity

| Key | Value |
|---|---|
| Project | `virtualfriend-demo` (number `159664521231`) |
| Local gcloud account | `virtualfriend@virtualfriend-demo.iam.gserviceaccount.com` |
| Instance service account | `159664521231-compute@developer.gserviceaccount.com` |
| Instance name | `vm` (one per zone; the same name exists in old and new zone during cutover) |
| Old zone / region | `us-west1-a` / `us-west1` |
| New zone / region | `us-south1-a` / `us-south1` |
| Old static IP | `ip-virtualfriend` = `34.145.45.178` |
| New static IP | `ip-virtualfriend-dallas` = `34.174.158.148` ✔ |
| Repo | `github.com/agilebean/virtualfriend`, checkout at `~/virtualfriend` (git root), app at `~/virtualfriend/src` |

## 2. Instance spec ✔

| Key | Value |
|---|---|
| Machine type | `n2-standard-2` (2 vCPU, 8 GB) |
| Provisioning | `SPOT`, `--instance-termination-action=STOP`, `--maintenance-policy=TERMINATE`, `--no-restart-on-failure` |
| Boot disk | `persistent-disk-0`, 12 GB, type PERSISTENT, `autoDelete=false` |
| Image | Ubuntu 24.04.3 LTS (`ubuntu-2404-lts`) |
| Network / subnet | `default` / `default`, one NIC, IPv4 only, Premium tier |
| Network tag | `allow-tcp-8080` |
| Scopes | `devstorage.read_only`, `logging.write`, `monitoring.write`, `service.management.readonly`, `servicecontrol`, `trace.append` |
| Metadata | `enable-oslogin=FALSE`, `serial-port-enable=true`, `startup-script`, `ssh-keys` |

Create command (this is the one that produced the Dallas instance):

```bash
gcloud compute addresses create ip-virtualfriend-dallas --region=us-south1
IP=$(gcloud compute addresses describe ip-virtualfriend-dallas --region=us-south1 --format="value(address)")

gcloud compute instances create vm --zone=us-south1-a \
  --machine-type=n2-standard-2 --provisioning-model=SPOT \
  --instance-termination-action=STOP --maintenance-policy=TERMINATE --no-restart-on-failure \
  --image=vm-cutover-20261118 --boot-disk-size=12GB --no-boot-disk-auto-delete \
  --address="$IP" --tags=allow-tcp-8080 \
  --metadata=enable-oslogin=FALSE,serial-port-enable=true \
  --metadata-from-file=startup-script=/tmp/vm_migrate/startup-script.sh,ssh-keys=/tmp/vm_migrate/ssh-keys \
  --service-account=159664521231-compute@developer.gserviceaccount.com \
  --scopes=https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/trace.append
```

Boot takes ~35 s and the app needs another ~60 s, so nothing answers for the first ~90 s. Probing at 60 s looks like a dead machine.

## 3. Startup script (metadata `startup-script`, 408 bytes) ✔

```bash
#!/bin/bash
set -x
exec &> /dev/ttyS0
echo "=== STARTUP CLEANUP ==="
# Free space
rm -rf /var/log/syslog /var/log/syslog.* /var/log/*.gz 2>/dev/null
journalctl --vacuum-size=5M 2>/dev/null || true
apt-get clean 2>/dev/null || true
rm -rf /var/cache/apt/archives/* 2>/dev/null || true
# Grow partition and filesystem
growpart /dev/sda 1
resize2fs /dev/sda1 || xfs_growfs / || true
df -h /
echo "=== DONE ==="
```

## 4. Firewall (project level, unchanged by the move)

| Rule | Direction | Source | Target tag | Ports |
|---|---|---|---|---|
| `allow-tcp-8080` | INGRESS | `0.0.0.0/0` | `allow-tcp-8080` | tcp:8080 |
| `allow-http` | INGRESS | `0.0.0.0/0` | — | tcp:80 |
| `allow-https` | INGRESS | `0.0.0.0/0` | — | tcp:443 |
| `default-allow-ssh` | INGRESS | `0.0.0.0/0` | — | tcp:22 |

## 5. DNS (Squarespace panel, zone on `ns-cloud-c1..c4.googledomains.com`)

| Record | Type | Data | Notes |
|---|---|---|---|
| `my` | A | instance IP | FastAPI app + OAuth callback |
| `api` | A | instance IP | same app, separate cert |
| `www` | CNAME | `virtualfriend.dcms.site` | Dorik, do not touch |
| apex `@` | A | `18.119.18.18` | Dorik, do not touch |

TTL on both A records: 300 s. Nothing in the Dorik pages or the repo references the IP, so DNS plus the SSH secret are the only address carriers.

## 6. Software ✔

- OS Ubuntu 24.04.3, 55 manual apt packages:
  `acl base-files bash bsdutils certbot chrony cloud-init curl dash diffutils eatmydata fail2ban findutils fuse3 gnupg google-compute-engine google-compute-engine-oslogin google-guest-agent google-osconfig-agent grep grub-pc gzip hostname init libeatmydata1 libwrap0 linux-base linux-gcp login mongodb-org ncurses-base ncurses-bin ncurses-term nginx openssh-server openssh-sftp-server python-babel-localedata python3-babel python3-certbot-nginx python3-jinja2 python3-json-pointer python3-jsonpatch python3-jsonschema python3-markupsafe python3-pyrsistent python3-serial python3-tz shim-signed ssh-import-id supervisor ubuntu-minimal ubuntu-server ubuntu-standard update-notifier-common util-linux`
- Conda: miniforge at `~/miniforge3` (2.8 GB), single env `virtualfriend`, Python 3.12.8.
- pip: 161 packages; repo `requirements.txt` has 146 pinned lines. Rebuild with `pip install -r requirements.txt` and reconcile against `pip freeze` from the old box.
- nltk `tokenizers` corpus at `~/nltk_data` (64 MB).
- `/usr/local/bin/cleanup-mongodb-diagnostics.sh` (deletes `metrics.*` older than 7 days).
- Do not upgrade pip packages during a rebuild: the deploy workflow copies `patches/pipecat/patch_langchain_processor.py` into site-packages, so versions are load-bearing.

## 7. Services

**nginx** (`sites-enabled`: `my.virtualfriend.chat`, `api.virtualfriend.chat`, `default`):

```
server_name my.virtualfriend.chat;   proxy_pass http://localhost:8080;
ssl_certificate /etc/letsencrypt/live/my.virtualfriend.chat/fullchain.pem;
server_name api.virtualfriend.chat;  proxy_pass http://localhost:8080;
ssl_certificate /etc/letsencrypt/live/api.virtualfriend.chat/fullchain.pem;
```

Both listen `0.0.0.0:80` and `0.0.0.0:443`; certs are certbot-managed, CN/SAN equal to the hostname, expiring 2027-01-18 (`my`) and 2027-01-22 (`api`).

**supervisor** (`/etc/supervisor/conf.d/fastapi_app.conf`):

```ini
[program:fastapi_app]
directory=/home/chaehan/virtualfriend/src
command=/home/chaehan/virtualfriend/src/scripts/start_fastapi_app.sh
user=chaehan
autostart=true
autorestart=true
stdout_logfile=/var/log/supervisor/fastapi_app.out.log
stderr_logfile=/var/log/supervisor/fastapi_app.error.log
environment=PATH="/home/chaehan/miniforge3/envs/virtualfriend/bin:%(ENV_PATH)s",PYTHONUNBUFFERED="1"
stopasgroup=true
killasgroup=true
stopsignal=QUIT
stopwaitsecs=10
stopcommand=/home/chaehan/virtualfriend/src/scripts/stop_fastapi_app.sh
```

`flask_app` also exists and has been FATAL for months (`exit status 127`). Drop it in a rebuild.

**cron**: `certbot` (`0 */12 * * *`, random sleep), `mongodb-cleanup` (`0 2 * * 0`), `sysstat`, `e2scrub_all`.

## 8. Bot defence: fail2ban ✔

`/etc/fail2ban/jail.d/fastapi_app.local`:

```ini
[fastapi_app]
enabled = true
port = 8080
filter = fastapi
logpath = /var/log/fastapi_app.access.log
maxretry = 3
bantime = -1
backend = polling
```

`/etc/fail2ban/filter.d/fastapi.conf`:

```ini
[Definition]
failregex = INFO:\s+<HOST>:\d+ - ".*" (?:400|403|404).*
ignoreregex =
```

`/etc/fail2ban/jail.local` sets `banaction = nftables`, `banaction_allports = nftables[type=allports]`, `backend = systemd`, and enables `[sshd]`.

Bans persist in `/var/lib/fail2ban/fail2ban.sqlite3` (3.3 MB). Carrying that file plus the two configs restores all **5398** bans at boot — verified on the Dallas instance.

## 9. Database ✔

| Key | Value |
|---|---|
| Version | mongod 7.0.25 |
| Config | `/etc/mongod.conf`: `dbPath=/var/lib/mongodb`, `bindIp=127.0.0.1`, `port=27017` |
| URI | `mongodb://127.0.0.1:27017` |
| Database | `test` (yes, that is the production name) |
| Collections | `memories` 112 docs, `settings` 1 doc, `locks` 0 docs |
| Indexes | `memories`: `email_1`, `user_id_1` (unique), text index on `conversation_summaries.**`; `locks`: `user_id_1` (unique) |

Move it with:

```bash
# old
mongodump --db test --out /tmp/dump
# new
mongorestore --drop --db test /tmp/dump/test
```

## 10. Secrets and credentials

Not in git. All must cross over; the `.env` must be `chmod 600` (it is `664` today).

| Item | Location | Notes |
|---|---|---|
| Env file, 60 keys | `~/virtualfriend/src/.env` | GROQ, GOOGLE, ANTHROPIC, OPENAI, ELEVENLABS, COHERE, DEEPGRAM, CARTESIA, LMNT (+URL), WHATSAPP (token, app secret, phone id, verify token), DAILY, MONGODB_URI, MONGODB_DB_NAME, GOOGLE_CLIENT_SECRETS_FILE, GOOGLE_APPLICATION_CREDENTIALS, GMAIL_CREDENTIALS_FILE, MICROSOFT_CLIENT_ID/SECRET, APPLE_CLIENT_SECRET, Stripe test and live (publishable, secret, webhook secret, 4 price ids, portal url, 3 payment links) |
| GCP service-account key | `~/virtualfriend/src/config/virtualfriend-demo.json` | read by `config/validation.py`; highest-value file on the box |
| OAuth client secrets | `config/gcloud_client_secret.json`, `config/client_secret_gmail.json` | |
| SSH | `~/.ssh/id_rsa`, `~/.ssh/authorized_keys` | regenerate host keys on a rebuild |
| Certbot | `/etc/letsencrypt/` (root) | reissue with HTTP-01; port 80 is open |
| Secret Manager | 14 secrets: `ANTHROPIC_API_KEY`, `APPLE_CLIENT_SECRET`, `DAILY_API_KEY`, `DEEPGRAM_API_KEY`, `ELEVENLABS_API_KEY`, `GOOGLE_API_KEY`, `GROQ_API_KEY`, `MICROSOFT_CLIENT_ID`, `MICROSOFT_CLIENT_SECRET`, `OPENAI_API_KEY`, `PLAYHT_API_KEY`, `PLAYHT_USER_ID`, `agilebean-github-oauthtoken-a775c9`, `gcloud-client-secret` | cost ~$0.83/month (2.8¢/day) |

## 11. Logs

| Path | Content | Synced by |
|---|---|---|
| `/var/log/fastapi_app.access.log` | app access log, fail2ban's input | `logsync` alias |
| `/var/log/fastapi_app.out.log`, `*.error.log` | supervisor stdout/stderr | `logsync` alias |
| `~/virtualfriend/src/logs/chats/` | per-call transcripts | `chatsync` alias |
| `~/virtualfriend/src/logs/mongodb/` | local `mongodump` copies | `mongodump_to_local.sh` |
| `/var/log/nginx/`, `/var/log/fail2ban.log*` | proxy and ban activity | manual rsync |
| `/var/log/syslog` | system | not carried (286 MB, noise) |

`bash scripts/datasync.sh` runs all three syncs and a health check. Rule for a rebuild: everything is synced down first, and only the last 30 days of app/chat logs are copied onto the new machine.

## 12. Deploy and monitoring plumbing

| Item | Value |
|---|---|
| Workflow | `.github/workflows/deploy.yml`, on push to `main`, `appleboy/ssh-action` |
| Secrets | `SSH_HOST` (the instance IP), `SSH_USER`, `SSH_PRIVATE_KEY` |
| Workflow body | `git stash`, `git fetch`, `git reset --hard origin/main`, copy `patches/pipecat/patch_langchain_processor.py` into the conda env, `sudo supervisorctl restart fastapi_app` |
| Log sink | `vm-preemption-sink`, filter `resource.type="gce_instance" AND protoPayload.methodName="compute.instances.preempted" AND resource.labels.instance_name="vm"` → `pubsub.googleapis.com/projects/virtualfriend-demo/topics/vm-preemptions` |
| Cloud Run function | `restart-vm-on-preemption`, us-central1, gen2, env `PROJECT_ID=virtualfriend-demo`, `VM_NAME=vm`, `ZONE=us-south1-a` |
| Function source | `cloudfunctions/vm_autorestart_cloudfunction/deploy.sh` (reads project and zone from gcloud config) |
| Local alias | `gc` = `gcloud compute ssh chaehan@vm` (needs `compute/zone` set to the live zone) |

## 13. One-shot sequence

1. `gcloud config set project virtualfriend-demo`; `gcloud config set compute/zone us-west1-a`.
2. Sync everything down: `bash scripts/datasync.sh`, plus the nginx and fail2ban log rsync, plus the ban export.
3. `gcloud compute instances stop vm --zone=us-west1-a` (29 s measured).
4. `gcloud compute images create vm-cutover-20261118 --source-disk=vm --source-disk-zone=us-west1-a --storage-location=us` (133 s measured, 12 GB).
5. `gcloud compute instances start vm --zone=us-west1-a` (13 s; `/health` 200 at 203 s).
6. `gcloud compute addresses create ip-virtualfriend-dallas --region=us-south1`.
7. `gcloud compute instances create vm --zone=us-south1-a …` (section 2); wait ~90 s for boot and app.
8. Verify (section 14) on the new IP.
9. Chaehan edits both A records in Squarespace; confirm with `dig +short my.virtualfriend.chat` and `api.…`.
10. `gh secret set SSH_HOST -R agilebean/virtualfriend --body <new ip>`; `gh workflow run deploy.yml`; confirm the run's log shows the new host.
11. Update the sink filter to `instance_name="vm"`, run `deploy.sh` with `ZONE=us-south1-a`, test with `gcloud compute instances simulate-maintenance-event`.
12. Delete the image once 8-11 pass; delete the old instance, disk and `ip-virtualfriend` after 7 quiet days.

## 14. Verification commands

```bash
IP=<new ip>
curl -s http://$IP:8080/health
curl -s -o /dev/null -w "%{http_code}\n" --resolve my.virtualfriend.chat:443:$IP  https://my.virtualfriend.chat/health
curl -s -o /dev/null -w "%{http_code}\n" --resolve api.virtualfriend.chat:443:$IP https://api.virtualfriend.chat/health
echo | openssl s_client -connect $IP:443 -servername my.virtualfriend.chat  2>/dev/null | openssl x509 -noout -subject -enddate
echo | openssl s_client -connect $IP:443 -servername api.virtualfriend.chat 2>/dev/null | openssl x509 -noout -subject -enddate
gcloud compute ssh chaehan@vm --zone=us-south1-a --command='sudo supervisorctl status; sudo fail2ban-client status; mongosh --quiet --eval "db.getSiblingDB(\"test\").memories.countDocuments()"; df -h /'
```

Expected on a healthy instance: `/health` JSON with `"status":"healthy"`, both hostnames 200, certificates matching their hostname with a 2027 expiry, `fastapi_app RUNNING`, `flask_app FATAL` (pre-existing), two fail2ban jails with 5398 bans, 112 documents, root disk ~67% used.
