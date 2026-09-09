# -*- coding: utf-8 -*-
"""查 9222 监听状态 + 本机连接测试(2026-09-09)"""
import socket, io, sys, subprocess

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

out = subprocess.run(["powershell", "-NoProfile", "-Command",
    "Get-NetTCPConnection -LocalPort 9222 -ErrorAction SilentlyContinue | Select-Object LocalAddress,LocalPort,State,OwningProcess | Format-Table -AutoSize"],
    capture_output=True, text=True, timeout=30).stdout
print("netstat 9222:", out or "(nothing)")

# 直连测试
for host, port in [("127.0.0.1", 9222), ("localhost", 9222)]:
    try:
        s = socket.create_connection((host, port), timeout=3)
        print(f"socket OK {host}:{port}")
        s.close()
    except Exception as e:
        print(f"socket FAIL {host}:{port}: {e}")
