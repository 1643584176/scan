# -*- coding: utf-8 -*-
"""诊断 Cookies 文件访问失败原因(2026-09-09)"""
import os, io, sys, ctypes

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DB = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Network\Cookies")
print("path:", DB, "exists:", os.path.exists(DB), "size:", os.path.getsize(DB) if os.path.exists(DB) else "-")

# 1. python open
try:
    with open(DB, "rb") as f:
        head = f.read(16)
    print("python open OK, head:", head[:8])
except Exception as e:
    print("python open ERR:", repr(e))

# 2. CreateFileW 正确错误码
GENERIC_READ = 0x80000000
FILE_SHARE_READ = 0x1
FILE_SHARE_WRITE = 0x2
FILE_SHARE_DELETE = 0x4
OPEN_EXISTING = 3
FILE_ATTRIBUTE_NORMAL = 0x80
INVALID_HANDLE = ctypes.c_void_p(-1).value

ctypes.windll.kernel32.SetLastError(0)
h = ctypes.windll.kernel32.CreateFileW(
    DB, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
    None, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, None)
err = ctypes.get_last_error()
print("CreateFileW handle:", h, "err:", err)
if h not in (0, INVALID_HANDLE):
    ctypes.windll.kernel32.CloseHandle(h)
