# -*- coding: utf-8 -*-
"""Real PG connection attempt: fetch role password via API then connect
to both ep-* host and pg.neon.tech.  Determine which auth paths work."""
import json
import time
import ssl
import socket
import http.client

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
HB = {"X-Bug-Bounty": "xxbo"}
PA = "orange-sun-90493739"
PAMAIN = "br-wandering-field-w2ob6mpn"
LOG = r"F:\scan\neon_report\_u5_out.txt"

with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]


def call(method, path, body=None, timeout=30):
    ctx = ssl.create_default_context()
    conn = http.client.HTTPSConnection(API_HOST, timeout=timeout, context=ctx)
    payload = json.dumps(body) if body is not None else None
    hdrs = dict(HB, Authorization="Bearer " + APIKEY)
    if body is not None:
        hdrs["Content-Type"] = "application/json"
    conn.request(method, API_BASE + path, body=payload, headers=hdrs)
    resp = conn.getresponse()
    data = resp.read().decode("utf-8", "replace")
    conn.close()
    return resp.status, data


def out(s):
    print(s, flush=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(s + "\n")


# 1. roles + databases
st, d = call("GET", "/projects/%s/branches/%s/roles" % (PA, PAMAIN))
out("== roles: %s %s" % (st, d[:600]))
st, d = call("GET", "/projects/%s/branches/%s/databases" % (PA, PAMAIN))
out("== databases: %s %s" % (st, d[:600]))

# 2. password retrieval candidates
pw = None
for p in (
    "/projects/%s/branches/%s/roles/neondb_owner/password" % (PA, PAMAIN),
    "/projects/%s/branches/%s/roles/neondb_owner/password/reveal" % (PA, PAMAIN),
    "/projects/%s/roles/neondb_owner/password" % PA,
):
    st, d = call("GET", p)
    out("== pw candidate %s -> %s %s" % (p.split("/projects/")[1], st, d[:400]))
    if st == 200:
        try:
            pw = json.loads(d).get("password")
        except Exception:
            pw = None
        if pw:
            break

# 3. try psycopg / pg8000
try:
    import psycopg
    MOD = "psycopg3"
except Exception:
    try:
        import psycopg2
        MOD = "psycopg2"
    except Exception:
        try:
            import pg8000
            MOD = "pg8000"
        except Exception:
            MOD = None
out("== pg driver: %s" % MOD)

if pw and MOD:
    params = dict(host="ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build",
                  user="neondb_owner", password=pw, dbname="neondb",
                  connect_timeout=10)
    try:
        if MOD == "psycopg3":
            import psycopg
            conn = psycopg.connect(**params, sslmode="require")
        elif MOD == "psycopg2":
            import psycopg2
            conn = psycopg2.connect(**params, sslmode="require")
        else:
            import pg8000
            conn = pg8000.connect(**params)
        cur = conn.cursor()
        cur.execute("select current_user, version()")
        out("== EP CONNECT OK: %r" % (cur.fetchone(),))
        conn.close()
    except Exception as e:
        out("== EP connect fail: %s: %s" % (type(e).__name__, str(e)[:300]))

    params2 = dict(params)
    params2["host"] = "pg.neon.tech"
    try:
        if MOD == "psycopg3":
            import psycopg
            conn = psycopg.connect(**params2, sslmode="require")
        elif MOD == "psycopg2":
            import psycopg2
            conn = psycopg2.connect(**params2, sslmode="require")
        else:
            import pg8000
            conn = pg8000.connect(**params2)
        cur = conn.cursor()
        cur.execute("select current_user, version()")
        out("== PG.NEON.TECH CONNECT OK: %r" % (cur.fetchone(),))
        conn.close()
    except Exception as e:
        out("== pg.neon.tech connect fail: %s: %s" % (type(e).__name__, str(e)[:300]))
elif not pw:
    out("== no password retrieved; need connection string from API")
    # try connection uri endpoint
    for p in ("/projects/%s/connection_uri" % PA,
              "/projects/%s/branches/%s/connection_uri" % (PA, PAMAIN)):
        st, d = call("GET", p)
        out("== connuri %s -> %s %s" % (p, st, d[:500]))
print("== DONE", flush=True)
