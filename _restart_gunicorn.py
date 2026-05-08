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


def run(client, cmd, total_timeout=90, ignore_error=False):
    print(f"\n$ {cmd}", flush=True)
    _, stdout, _ = client.exec_command(cmd, get_pty=True)
    channel = stdout.channel
    channel.settimeout(0.0)
    buf = ""
    deadline = time.time() + total_timeout
    ansi = re.compile(r"\x1b\[[0-9;]*[A-Za-z]|\r")
    while True:
        if time.time() > deadline:
            break
        readable, _, _ = select.select([channel], [], [], 2.0)
        if readable:
            try:
                chunk = channel.recv(4096)
            except Exception:
                break
            if not chunk:
                break
            text = ansi.sub("", chunk.decode("utf-8", errors="replace"))
            print(text, end="", flush=True)
            buf += text
        elif channel.exit_status_ready():
            break
    status = channel.recv_exit_status()
    if status not in (0, -1) and not ignore_error:
        raise RuntimeError(f"Command failed with exit {status}: {cmd}")
    return buf


env = read_env(ROOT / ".env")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(env["vps_ip"], username=env["vps_un"], password=env["vps_pw"], timeout=20)
print("Connected to VPS")

print("\n===== Kill any stale gunicorn =====")
run(client, "pkill -f '[g]unicorn.*app.main:app' || true", ignore_error=True)
time.sleep(2)

print("\n===== Start gunicorn daemon =====")
run(client, f"cd {DEPLOY_DIR} && venv/bin/gunicorn -c gunicorn.py app.main:app --daemon", ignore_error=True)
time.sleep(6)

print("\n===== Health checks =====")
run(client, "pgrep -af '[g]unicorn.*app.main:app'")
run(client, "ss -tlnp | grep 8999")
run(client, "curl -sS --max-time 10 http://127.0.0.1:8999/api/geo/check | head -c 300")
run(client, "tail -10 /var/log/roxy.log")

client.close()
print("\nDone.")
