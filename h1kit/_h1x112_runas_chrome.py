# -*- coding: utf-8 -*-
"""runas 启动 Chrome(带调试端口)+ 轮询 CDP(2026-09-09)"""
import subprocess, time, io, sys, urllib.request, ctypes

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

def cdp_alive():
    try:
        with urllib.request.urlopen("http://127.0.0.1:9222/json/version", timeout=2) as r:
            return r.read().decode()[:150]
    except Exception:
        return None

# ShellExecuteW runas → 弹 UAC
res = ctypes.windll.shell32.ShellExecuteW(None, "runas", CHROME, "--remote-debugging-port=9222", None, 1)
print("ShellExecuteW ret:", res, "(>32 = ok, 1223 = user cancelled)", flush=True)

for i in range(60):
    time.sleep(1)
    v = cdp_alive()
    if v:
        print("CDP ALIVE:", v, flush=True)
        break
    if i % 5 == 0 and i > 0:
        print(f"  waiting CDP... t+{i}s", flush=True)
else:
    print("CDP NOT UP after 60s", flush=True)
