# -*- coding: utf-8 -*-
"""elevated 执行 ps1 → 轮询 CDP(2026-09-09)"""
import time, io, sys, urllib.request, ctypes

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PS1 = r"D:\scan\h1kit\_h1x114_relaunch.ps1"

def cdp_alive():
    try:
        with urllib.request.urlopen("http://127.0.0.1:9222/json/version", timeout=2) as r:
            return r.read().decode()[:150]
    except Exception:
        return None

cmd = f"powershell -NoProfile -ExecutionPolicy Bypass -File \"{PS1}\""
res = ctypes.windll.shell32.ShellExecuteW(None, "runas", "powershell", cmd, None, 0)
print("ShellExecuteW ret:", res, "(>32 ok)", flush=True)

for i in range(90):
    time.sleep(1)
    v = cdp_alive()
    if v:
        print("CDP ALIVE:", v, flush=True)
        break
    if i % 5 == 0:
        print(f"  waiting t+{i}s", flush=True)
else:
    print("CDP NOT UP after 90s", flush=True)
