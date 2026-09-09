# -*- coding: utf-8 -*-
"""Chrome profiles + 进程命令行(2026-09-09)"""
import os, io, sys, subprocess, json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
profs = [d for d in os.listdir(BASE) if os.path.isdir(os.path.join(BASE, d)) and d not in ("ShaderCache", "GrShaderCache", "DawnCache", "Crashpad", "BrowserMetrics", "Component Updater")]
print("profiles:", profs)

# 命令行(取主进程)
out = subprocess.run(["powershell", "-NoProfile", "-Command",
    "Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | Select-Object -First 3 -ExpandProperty CommandLine"],
    capture_output=True, text=True, timeout=60).stdout
print("chrome cmdline:\n", out[:2500])
