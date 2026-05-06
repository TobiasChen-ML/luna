# Roxy VPS Deployment

Last updated: 2026-05-04

Deployments must be pull-based on the VPS. Do not upload a local source archive
or any local database file to the server.

## 1. Local Release

Run from the repository root:

```bash
git status --short
git branch --show-current
git rev-parse --short HEAD
```

Build and test the intended release locally:

```bash
cd frontend
npm run build
```

Commit and push the release:

```bash
git add <changed files>
git commit -m "Deploy latest Roxy updates"
git push luna main
```

The VPS deployment starts only after the push succeeds.

## 2. VPS Layout

- Source workspace: `/opt/roxy-repo`
- Live deployment: `/opt/roxy`
- Live backend package: `/opt/roxy/app`
- Live static files: `/opt/roxy/dist`
- Runtime database: `/opt/roxy/roxy.db`
- Runtime log: `/var/log/roxy.log`

`/opt/roxy/roxy.db` is production runtime data. It must never be committed,
uploaded from local, copied from `/opt/roxy-repo`, or replaced during deploy.

## 3. Pull On VPS

Run on the VPS:

```bash
cd /opt/roxy-repo
git fetch origin
git reset --hard origin/main
git clean -fd --exclude=.env --exclude='*.db' --exclude='*.sqlite' --exclude='*.sqlite3'
git log --oneline -3
```

Before syncing, verify the repo does not track database files:

```bash
cd /opt/roxy-repo
git ls-files | grep -E '(^|/)(roxy\.db|app\.db|.*\.sqlite3?|.*\.db)$' && exit 1 || true
test -f /opt/roxy/roxy.db
```

## 4. Sync Backend Code

Only sync code and requirements:

```bash
rsync -av --delete --exclude='__pycache__' --exclude='*.pyc' \
  /opt/roxy-repo/backend/app/ /opt/roxy/app/

cp /opt/roxy-repo/backend/requirements.txt /opt/roxy/requirements.txt
cd /opt/roxy && venv/bin/pip install -q -r requirements.txt
```

Do not run commands that copy `backend/roxy.db`, `roxy.db`, `app.db`, or any
SQLite/WAL/SHM file into `/opt/roxy`.

## 5. Frontend Static Files

Preferred path: build on CI or a controlled local machine, then publish static
assets through a separate artifact flow that contains only `frontend/dist`.

If syncing from the VPS repo, only use an already-built `frontend/dist`:

```bash
test -f /opt/roxy-repo/frontend/dist/index.html
ts=$(date +%Y%m%d%H%M%S)
cp -r /opt/roxy/dist /opt/roxy/dist.prev.$ts 2>/dev/null || true
rsync -av --delete /opt/roxy-repo/frontend/dist/ /opt/roxy/dist/
```

Do not run `npm install` or `npm run build` on the VPS unless memory has been
explicitly increased.

## 6. Restart Gunicorn

Use `--daemon`; do not rely on backgrounding with `nohup` inside an SSH session.

```bash
pkill -f '[g]unicorn.*app.main:app' || true
sleep 2
cd /opt/roxy && venv/bin/gunicorn -c gunicorn.py app.main:app --daemon
sleep 5
```

## 7. Health Checks

Run on the VPS:

```bash
pgrep -af '[g]unicorn.*app.main:app'
ss -tlnp | grep 8999
curl -I --max-time 10 http://127.0.0.1:8999/
curl -sS --max-time 10 http://127.0.0.1:8999/api/geo/check | head -c 500
systemctl status nginx --no-pager -l
nginx -t
curl -I --max-time 10 http://127.0.0.1/
```

Expected result:

- Gunicorn master and workers are running.
- Gunicorn listens on `0.0.0.0:8999`.
- `/api/geo/check` returns JSON.
- nginx is active and config validates.

## 8. Automation

`python _deploy.py` follows this pull-based flow:

- reads VPS credentials from root `.env`;
- runs `git fetch/reset` on `/opt/roxy-repo`;
- refuses deploy if DB files are tracked by Git;
- syncs only backend code from `/opt/roxy-repo/backend/app/`;
- restarts gunicorn and runs health checks.
