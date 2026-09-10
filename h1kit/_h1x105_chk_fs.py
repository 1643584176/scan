# -*- coding: utf-8 -*-
"""检查 Chrome 安装路径与 Network 目录文件(2026-09-09)"""
import os, io, sys, subprocess

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# 1. chrome 进程路径
try:
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          "Get-Process chrome -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Path"],
                         capture_output=True, text=True, timeout=30).stdout.strip()
    print("chrome path:", out)
except Exception as e:
    print("ps err", e)

# 2. Network 目录
d = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Network")
if os.path.isdir(d):
    for fn in os.listdir(d):
        p = os.path.join(d, fn)
        print(os.path.getsize(p), fn)
else:
    print("no dir:", d)

# 3. Local State 存在性
ls = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Local State")
print("LocalState exists:", os.path.exists(ls))
