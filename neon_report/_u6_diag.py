# -*- coding: utf-8 -*-
import json, ssl, http.client, sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pg import connect, query

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
HB = {"X-Bug-Bounty": "xxbo"}
PA = "orange-sun-90493739"

with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]

ctx = ssl.create_default_context()
conn = http.client.HTTPSConnection(API_HOST, timeout=30, context=ctx)
conn.request("GET", API_BASE + "/projects/%s/connection_uri?database_name=neondb&role_name=neondb_owner&branch_id=br-lively-moon-w2v8u44x" % PA,
             headers=dict(HB, Authorization="Bearer " + APIKEY))
r = conn.getresponse()
d = r.read().decode("utf-8", "replace")
conn.close()
print("uri:", r.status)
from urllib.parse import urlsplit
u = urlsplit(json.loads(d)["uri"])
print("host:", u.hostname)

pg = connect(u.hostname, u.username, u.password)
cur = pg.cursor()
for sql in ("select version()",
            "create table if not exists u6_pii(id int, email text, name text)",
            "delete from u6_pii",
            "insert into u6_pii values (1,'alice.real@victimcorp.com','Alice')",
            "select * from u6_pii"):
    try:
        cur.execute(sql)
        try:
            print("OK:", sql[:50], "->", cur.fetchall())
        except Exception as e:
            print("OK(no rows):", sql[:50], type(e).__name__)
    except Exception as e:
        print("FAIL:", sql[:50], type(e).__name__, str(e)[:200])
pg.close()
