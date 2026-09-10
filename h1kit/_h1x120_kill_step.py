# -*- coding: utf-8 -*-
"""step1: elevated 杀光 Chrome(2026-09-09)"""
import ctypes, time, io, sys, subprocess

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

kill_ps1 = r"D:\scan\h1kit\_h1x119_kill.ps1"
cmd = f"powershell -NoProfile -ExecutionPolicy Bypass -File \"{kill_ps1}\""
print("launching elevated kill (UAC)...", flush=True)
res = ctypes.windll.shell32.ShellExecuteW(None, "runas", "powershell", cmd, None, 0)
print("ShellExecuteW ret:", res, flush=True)
time.sleep(8)

def chrome_count():
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
        "(Get-Process chrome -ErrorAction SilentlyContinue | Measure-Object).Count"],
        capture_output=True, text=True, timeout=30).stdout.strip()
    try:
        return int(out)
    except Exception:
        return -1

print("chrome procs:", chrome_count(), flush=True)
