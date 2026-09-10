# -*- coding: utf-8 -*-
"""枚举 Chrome profiles 找 hackerone cookie(只读直开 + WAL)(2026-09-09)"""
import os, sqlite3, io, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
profiles = [d for d in os.listdir(BASE) if d.startswith(("Default", "Profile")) and os.path.isdir(os.path.join(BASE, d))]

for prof in profiles:
    db = os.path.join(BASE, prof, "Network", "Cookies")
    if not os.path.exists(db):
        continue
    uri = "file:" + db.replace("\\", "/") + "?mode=ro&immutable=1"
    try:
        con = sqlite3.connect(uri, uri=True)
        cur = con.cursor()
        cur.execute("SELECT host_key, name, length(value), substr(hex(value),1,8) FROM cookies WHERE host_key LIKE '%hackerone%'")
        rows = cur.fetchall()
        print(f"[{prof}] hackerone cookies: {len(rows)}")
        for host, name, ln, prefix in rows:
            print(f"  {host:40s} {name:35s} len={ln:6d} hex={prefix}")
        con.close()
    except Exception as e:
        print(f"[{prof}] ERR {repr(e)}")
