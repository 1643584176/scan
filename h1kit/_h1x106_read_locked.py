# -*- coding: utf-8 -*-
"""尝试多种方式读取被 Chrome 锁定的 Cookies(2026-09-09)"""
import os, sqlite3, io, sys, shutil

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DB = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Network\Cookies")
TMP = DB + ".bak_h1"

# 1. ctypes CreateFileW 带全共享 + 手动复制
import ctypes
from ctypes import wintypes

GENERIC_READ = 0x80000000
FILE_SHARE_READ = 0x1
FILE_SHARE_WRITE = 0x2
FILE_SHARE_DELETE = 0x4
OPEN_EXISTING = 3
FILE_ATTRIBUTE_NORMAL = 0x80

h = ctypes.windll.kernel32.CreateFileW(
    DB, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
    None, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, None)
if h == -1 or h == 0xFFFFFFFFFFFFFFFF:
    print("CreateFileW failed, err:", ctypes.get_last_error())
else:
    print("CreateFileW OK handle:", h)
    size = os.path.getsize(DB)
    buf = ctypes.create_string_buffer(size)
    read = wintypes.DWORD(0)
    ok = ctypes.windll.kernel32.ReadFile(h, buf, size, ctypes.byref(read), None)
    print("ReadFile ok:", bool(ok), "read:", read.value)
    ctypes.windll.kernel32.CloseHandle(h)
    if ok and read.value == size:
        with open(TMP, "wb") as f:
            f.write(buf.raw)
        print("saved copy:", TMP, size)

# 2. 尝试普通 connect(非 URI)
for label, path in [("direct", DB), ("copy", TMP)]:
    if not os.path.exists(path):
        continue
    try:
        con = sqlite3.connect(path)
        cur = con.cursor()
        cur.execute("SELECT count(*) FROM cookies")
        n = cur.fetchone()[0]
        print(f"[{label}] total cookies: {n}")
        cur.execute("SELECT host_key, name, length(value), substr(hex(value),1,8) FROM cookies WHERE host_key LIKE '%hackerone%'")
        for host, name, ln, prefix in cur.fetchall()[:20]:
            print(f"  {host:40s} {name:30s} len={ln:6d} hex={prefix}")
        con.close()
        break
    except Exception as e:
        print(f"[{label}] ERR {repr(e)}")
