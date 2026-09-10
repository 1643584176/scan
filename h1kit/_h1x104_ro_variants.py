# -*- coding: utf-8 -*-
"""只读打开尝试变体:immutable 开/关 + Edge(2026-09-09)"""
import os, sqlite3, io, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

def probe(db, label):
    if not os.path.exists(db):
        print(f"[{label}] no db")
        return
    for extra in ("&immutable=1", ""):
        uri = "file:" + db.replace("\\", "/") + "?mode=ro" + extra
        try:
            con = sqlite3.connect(uri, uri=True)
            cur = con.cursor()
            cur.execute("SELECT count(*) FROM cookies")
            n = cur.fetchone()[0]
            cur.execute("SELECT host_key, name, length(value), substr(hex(value),1,8) FROM cookies WHERE host_key LIKE '%hackerone%'")
            rows = cur.fetchall()
            print(f"[{label} extra='{extra}'] total={n} h1={len(rows)}")
            for host, name, ln, prefix in rows[:15]:
                print(f"    {host:40s} {name:30s} len={ln:6d} hex={prefix}")
            con.close()
            return
        except Exception as e:
            print(f"[{label} extra='{extra}'] ERR {repr(e)}")

CHROME_DEF = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Network\Cookies")
EDGE_DEF = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Network\Cookies")
probe(CHROME_DEF, "chrome-default")
probe(EDGE_DEF, "edge-default")
