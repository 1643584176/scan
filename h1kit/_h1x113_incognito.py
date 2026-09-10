# -*- coding: utf-8 -*-
"""检查 Chrome 状态 → 无痕 + 调试端口启动(2026-09-09)"""
import subprocess, time, io, sys, urllib.request, ctypes

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

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

n = chrome_count()
print("chrome procs:", n, flush=True)
if n > 0:
    print("closing chrome...", flush=True)
    subprocess.run(["powershell", "-NoProfile", "-Command",
        "Stop-Process -Name chrome -Force -ErrorAction SilentlyContinue"],
        capture_output=True, timeout=60)
    time.sleep(3)
    print("after kill:", chrome_count(), flush=True)

# runas 启动无痕 + 调试端口(带 UAC 弹窗)
res = ctypes.windll.shell32.ShellExecuteW(None, "runas", CHROME,
        "--incognito --remote-debugging-port=9222 https://hackerone.com", None, 1)
print("ShellExecuteW ret:", res, flush=True)

for i in range(60):
    time.sleep(1)
    v = cdp_alive()
    if v:
        print("CDP ALIVE:", v, flush=True)
        break
    if i % 5 == 0:
        print(f"  waiting CDP t+{i}s", flush=True)
else:
    print("CDP NOT UP after 60s", flush=True)
