# -*- coding: utf-8 -*-
"""查 chrome 主进程命令行是否带调试参数(2026-09-09)"""
import subprocess, io, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

out = subprocess.run(["powershell", "-NoProfile", "-Command",
    "Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | ForEach-Object { $_.CommandLine } | Select-String -Pattern 'remote-debugging|incognito' | Select-Object -First 5"],
    capture_output=True, text=True, timeout=60).stdout
print("matches:", out[:2000] if out else "(none)")

# 主进程(browser)命令行
out2 = subprocess.run(["powershell", "-NoProfile", "-Command",
    "Get-CimInstance Win32_Process -Filter \"Name='chrome.exe' and CommandLine not like '%--type=%'\" | ForEach-Object { $_.CommandLine }"],
    capture_output=True, text=True, timeout=60).stdout
print("browser cmdline:", out2[:2000] if out2 else "(none)")
