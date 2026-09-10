# -*- coding: utf-8 -*-
"""轮询等 Chrome 退出 → 带调试端口重启(2026-09-09)"""
import subprocess, time, io, sys, urllib.request, os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

def chrome_count():
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
        "(Get-Process chrome -ErrorAction SilentlyContinue | Measure-Object).Count"],
        capture_output=True, text=True, timeout=30).stdout.strip()
    try:
        return int(out)
    except Exception:
        return -1

def cdp_alive():
    try:
        with urllib.request.urlopen("http://127.0.0.1:9222/json/version", timeout=2) as r:
            return r.read().decode()[:120]
    except Exception:
        return None

print("waiting for chrome to exit...", flush=True)
for i in range(120):
    n = chrome_count()
    if n <= 0:
        print(f"chrome exited after ~{i*5}s", flush=True)
        break
    if i % 6 == 0:
        print(f"  still running: {n} procs (t+{i*5}s)", flush=True)
    time.sleep(5)
else:
    print("TIMEOUT: chrome still running after 600s", flush=True)
    sys.exit(1)

# 启动带调试端口(后台 detached,复用 Default profile)
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
subprocess.Popen([CHROME, "--remote-debugging-port=9222"],
                 creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                 close_fds=True)
print("chrome launched with --remote-debugging-port=9222", flush=True)

for i in range(30):
    time.sleep(1)
    v = cdp_alive()
    if v:
        print("CDP ALIVE:", v, flush=True)
        break
else:
    print("CDP NOT UP after 30s", flush=True)
