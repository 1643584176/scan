# -*- coding: utf-8 -*-
"""枚举 Chrome profiles 找 hackerone.com cookie(2026-09-09)"""
import os, sqlite3, shutil, glob, io, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
if not os.path.exists(BASE):
    print("no chrome:", BASE)
    sys.exit(0)

profiles = [d for d in os.listdir(BASE) if d in ("Default", "Profile 1", "Profile 2", "Profile 3", "Profile 4", "Profile 5", "Guest Profile")]

for prof in profiles:
    db = os.path.join(BASE, prof, "Network", "Cookies")
    if not os.path.exists(db):
        print(f"[{prof}] no Cookies db")
        continue
    tmp = db + ".h1tmp"
    try:
        shutil.copy2(db, tmp)
        con = sqlite3.connect(tmp)
        cur = con.cursor()
        cur.execute("SELECT host_key, name, length(value), substr(hex(value),1,8) FROM cookies WHERE host_key LIKE '%hackerone%' OR host_key LIKE '%hacker0x01%'")
        rows = cur.fetchall()
        print(f"[{prof}] hackerone cookies: {len(rows)}")
        for host, name, ln, prefix in rows:
            print(f"  {host:40s} {name:35s} len={ln:6d} hex={prefix}")
        con.close()
    except Exception as e:
        print(f"[{prof}] ERR {e}")
    finally:
        try:
            os.remove(tmp)
        except Exception:
            pass
