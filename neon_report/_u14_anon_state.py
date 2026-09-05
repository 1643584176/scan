# -*- coding: utf-8 -*-
"""ANGLE-5: anonymization state machine remaining unknowns.
A) start_anonymization=false branch: RA? data original or masked? dataplane?
B) successful anon branch: does GET branch still carry all 3 RA items after
   completion (dataplane already reachable => which RA actually enforced)?
C) restricted_actions item 3: delete-rw-endpoint - enforced? create new
   endpoint on restricted branch - allowed?
"""
import json
import time
import ssl
import http.client
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pg import connect, query

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
HB = {"X-Bug-Bounty": "xxbo"}
PA = "orange-sun-90493739"
PAMAIN = "br-wandering-field-w2ob6mpn"
LOG = r"F:\scan\neon_report\_u14_out.txt"

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


def pw_of(bid):
    st, d = call("GET", "/projects/%s/connection_uri?database_name=neondb&role_name=neondb_owner&branch_id=%s" % (PA, bid))
    if st != 200:
        return None
    from urllib.parse import urlsplit
    u = urlsplit(json.loads(d)["uri"])
    return u.hostname, u.username, u.password


def dselect(hp, tag, tries=12, wait=5):
    if not hp:
        return False, "no-hp"
    for i in range(tries):
        try:
            c = connect(*hp)
            rows = query(c, "select * from u14_pii")
            c.close()
            return True, repr(rows)
        except Exception as e:
            last = str(e)[:110]
            time.sleep(wait)
    return False, last


def wait_ready(bid, tries=20, wait=5):
    for i in range(tries):
        st, d = call("GET", "/projects/%s/branches/%s" % (PA, bid))
        try:
            b = json.loads(d)["branch"]
            if b.get("current_state") == "ready":
                return b
        except Exception:
            pass
        time.sleep(wait)
    return None


# cleanup u14 leftovers
st, d = call("GET", "/projects/%s/branches" % PA)
for b in json.loads(d).get("branches", []):
    if b.get("name", "").startswith("u14-"):
        call("DELETE", "/projects/%s/branches/%s" % (PA, b["id"]))
        out("cleaned %s" % b["name"])
time.sleep(2)

# ---- 1. src + data ----
st, d = call("POST", "/projects/%s/branches" % PA,
             {"branch": {"name": "u14-src", "parent_id": PAMAIN},
              "endpoints": [{"type": "read_write"}]})
SRC = json.loads(d)["branch"]["id"]
out("src=%s create:%s" % (SRC, st))
hp = None
for i in range(15):
    hp = pw_of(SRC)
    if hp:
        break
    time.sleep(4)
conn = None
for i in range(15):
    try:
        conn = connect(*hp)
        break
    except Exception:
        time.sleep(4)
query(conn, "create table if not exists u14_pii(id int, email text)")
query(conn, "delete from u14_pii")
query(conn, "insert into u14_pii values (1,'alice.real@victimcorp.com'),(2,'bob.ceo@victimcorp.com')")
out("src seeded: %s" % repr(query(conn, "select * from u14_pii")))
conn.close()

# ---- A. start_anonymization = false ----
st, d = call("POST", "/projects/%s/branch_anonymized" % PA, {
    "branch_create": {"branch": {"name": "u14-nostart", "parent_id": SRC},
                      "endpoints": [{"type": "read_write"}]},
    "masking_rules": [{
        "database_name": "neondb", "schema_name": "public",
        "table_name": "u14_pii", "column_name": "email",
        "masking_function": "anon.fake_email()"}],
    "start_anonymization": False,
})
out("A) nostart create: %s %s" % (st, d[:250]))
if st in (200, 201):
    NST = json.loads(d)["branch"]["id"]
    out("A) nostart ra=%s" % json.loads(d)["branch"].get("restricted_actions"))
    time.sleep(4)
    b = wait_ready(NST, tries=12, wait=5)
    out("A) nostart ready state=%s" % (b.get("current_state") if b else None))
    ok, data = dselect(pw_of(NST), "nostart", tries=8, wait=5)
    out("A) nostart dataplane: ok=%s data=%s" % (ok, data))
    st2, d2 = call("GET", "/projects/%s/branches/%s/anonymized_status" % (PA, NST))
    out("A) nostart anon_status: %s %s" % (st2, d2[:200]))
    # can we start the job later via any endpoint? probe PATCH + known names
    for meth, path, body in [
        ("POST", "/projects/%s/branches/%s/anonymize" % (PA, NST), {}),
        ("POST", "/projects/%s/branches/%s/start_anonymization" % (PA, NST), {}),
    ]:
        st3, d3 = call(meth, path, body)
        out("A) probe %s -> %s %s" % (path.split("/")[-1], st3, d3[:150]))
    call("DELETE", "/projects/%s/branches/%s" % (PA, NST))
    out("A) cleaned nostart")

# ---- B/C. successful anon branch ----
st, d = call("POST", "/projects/%s/branch_anonymized" % PA, {
    "branch_create": {"branch": {"name": "u14-ok", "parent_id": SRC},
                      "endpoints": [{"type": "read_write"}]},
    "masking_rules": [{
        "database_name": "neondb", "schema_name": "public",
        "table_name": "u14_pii", "column_name": "email",
        "masking_function": "anon.fake_email()"}],
    "start_anonymization": True,
})
out("B) ok create: %s %s" % (st, d[:250]))
OKB = json.loads(d)["branch"]["id"]
# wait for anon done
for i in range(24):
    time.sleep(5)
    st2, d2 = call("GET", "/projects/%s/branches/%s/anonymized_status" % (PA, OKB))
    if '"state":"anonymized"' in d2 or "anonymized" in d2.lower() and "failed" not in d2.lower():
        if "running" not in d2.lower() and "pending" not in d2.lower():
            out("B) anon done: %s" % d2[:200])
            break
b = wait_ready(OKB, tries=10, wait=5)
st3, d3 = call("GET", "/projects/%s/branches/%s" % (PA, OKB))
try:
    bj = json.loads(d3)["branch"]
    out("B) GET branch ra=%s" % bj.get("restricted_actions"))
except Exception:
    out("B) GET branch raw: %s" % d3[:400])
ok, data = dselect(pw_of(OKB), "ok", tries=10, wait=5)
out("B) ok dataplane (masked expected): ok=%s data=%s" % (ok, data))

# C) endpoint ops on restricted branch
st4, d4 = call("GET", "/projects/%s/branches/%s/endpoints" % (PA, OKB))
out("C) list endpoints: %s %s" % (st4, d4[:250]))
EP = None
try:
    eps = json.loads(d4).get("endpoints", [])
    EP = eps[0]["id"] if eps else None
except Exception:
    pass
if EP:
    st5, d5 = call("DELETE", "/projects/%s/endpoints/%s" % (PA, EP))
    out("C) DELETE rw endpoint on restricted br: %s %s" % (st5, d5[:250]))
    # recreate if deleted (to keep branch usable for cleanup)
    if st5 in (200, 202):
        st6, d6 = call("POST", "/projects/%s/branches/%s/endpoints" % (PA, OKB),
                       {"type": "read_write"})
        out("C) recreate endpoint: %s %s" % (st6, d6[:200]))
st7, d7 = call("POST", "/projects/%s/branches/%s/endpoints" % (PA, OKB),
               {"type": "read_only"})
out("C) create read_only endpoint on restricted br: %s %s" % (st7, d7[:250]))
if st7 in (200, 201, 202):
    call("DELETE", "/projects/%s/endpoints/%s" % (PA, json.loads(d7)["endpoint"]["id"]))
    out("C) cleaned extra endpoint")

# cleanup
call("DELETE", "/projects/%s/branches/%s" % (PA, OKB))
call("DELETE", "/projects/%s/branches/%s" % (PA, SRC))
out("cleanup done")
print("== DONE", flush=True)
