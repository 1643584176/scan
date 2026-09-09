# -*- coding: utf-8 -*-
"""检测 chrome 进程状态 + websocket 库可用性(2026-09-09)"""
import os, io, sys, subprocess

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

out = subprocess.run(["powershell", "-NoProfile", "-Command",
    "(Get-Process chrome -ErrorAction SilentlyContinue | Measure-Object).Count"],
    capture_output=True, text=True, timeout=30).stdout.strip()
print("chrome processes:", out)

try:
    import websocket
    print("websocket-client OK", getattr(websocket, "__version__", "?"))
except ImportError as e:
    print("websocket-client MISSING")

import urllib.request
try:
    with urllib.request.urlopen("http://127.0.0.1:9222/json/version", timeout=2) as r:
        print("CDP 9222 ALIVE:", r.read().decode()[:200])
except Exception as e:
    print("CDP 9222 down:", repr(e))
