import paramiko
import re
import select
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEPLOY_DIR = "/opt/roxy"


def read_env(path: Path) -> dict:
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key, value = stripped.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def run_raw(client, cmd, total_timeout=30):
    print(f"\n$ {cmd}", flush=True)
    _, stdout, stderr = client.exec_command(cmd)
    channel = stdout.channel
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    status = channel.recv_exit_status()
    if out:
        print(out)
    if err:
        print("[STDERR]", err)
    print(f"[exit {status}]")
    return out, err, status


env = read_env(ROOT / ".env")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(env["vps_ip"], username=env["vps_un"], password=env["vps_pw"], timeout=20)
print("Connected to VPS")

# check gunicorn config
run_raw(client, f"cat {DEPLOY_DIR}/gunicorn.py")

# try starting without daemon to capture errors
run_raw(client, f"cd {DEPLOY_DIR} && timeout 5 venv/bin/gunicorn -c gunicorn.py app.main:app 2>&1 | head -40 || true")

# check recent log
run_raw(client, "tail -30 /var/log/roxy.log")

client.close()
