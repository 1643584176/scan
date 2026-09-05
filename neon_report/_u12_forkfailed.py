# -*- coding: utf-8 -*-
"""ANGLE-1B: fork a FAILED anonymized branch (current state, no PITR args).
The masking job failed => 0 rows changed => branch holds FULL original data,
but dataplane is disabled + restricted_actions kept. Is fork (201, allowed)
the escape hatch that yields an unrestricted child with original data?
Also test DELETE -> recover cycle on the failed branch (does RA survive?)."""
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
LOG = r"F:\scan\neon_report\_u12_out.txt"

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


def dselect(hp, tag, tries=15, wait=4):
    """connect + select u12_pii; returns (ok, data_str)"""
    if not hp:
        return False, "no-hp"
    for i in range(tries):
        try:
            c = connect(*hp)
            rows = query(c, "select * from u12_pii")
            c.close()
            return True, repr(rows)
        except Exception as e:
            last = str(e)[:120]
            time.sleep(wait)
    return False, last


# cleanup u12 leftovers
st, d = call("GET", "/projects/%s/branches" % PA)
for b in json.loads(d).get("branches", []):
    if b.get("name", "").startswith("u12-"):
        call("DELETE", "/projects/%s/branches/%s" % (PA, b["id"]))
        out("cleaned %s" % b["name"])
time.sleep(2)

# ---- 1. src + data ----
st, d = call("POST", "/projects/%s/branches" % PA,
             {"branch": {"name": "u12-src", "parent_id": PAMAIN},
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
query(conn, "create table if not exists u12_pii(id int, email text, secret text)")
query(conn, "delete from u12_pii")
query(conn, "insert into u12_pii values (1,'alice.real@victimcorp.com','ssn-111'),(2,'bob.ceo@victimcorp.com','ssn-222'),(3,'carol.vp@victimcorp.com','ssn-333')")
out("src seeded: %s" % repr(query(conn, "select * from u12_pii")))
conn.close()

# ---- 2. failed anonymized branch (bad function) ----
st, d = call("POST", "/projects/%s/branch_anonymized" % PA, {
    "branch_create": {"branch": {"name": "u12-fail", "parent_id": SRC},
                      "endpoints": [{"type": "read_write"}]},
    "masking_rules": [{
        "database_name": "neondb", "schema_name": "public",
        "table_name": "u12_pii", "column_name": "email",
        "masking_function": "anon.no_such_fn()"}],
    "start_anonymization": True,
})
out("fail create: %s %s" % (st, d[:200]))
FAIL = json.loads(d)["branch"]["id"]
# wait for error state
for i in range(20):
    time.sleep(5)
    st2, d2 = call("GET", "/projects/%s/branches/%s/anonymized_status" % (PA, FAIL))
    if "error" in d2.lower():
        out("failed state confirmed: %s" % d2[:200])
        break
out("fail hp dataplane (should be disabled): %s" % repr(dselect(pw_of(FAIL), "fail", tries=2, wait=1)))

# ---- 3. fork failed branch CURRENT STATE (no lsn) ----
st, d = call("POST", "/projects/%s/branches" % PA,
             {"branch": {"name": "u12-fork", "parent_id": FAIL},
              "endpoints": [{"type": "read_write"}]})
out("fork failed-br create: %s %s" % (st, d[:300]))
FK = json.loads(d)["branch"]["id"]
out("fork branch ra=%s parent_lsn=%s" % (
    json.loads(d)["branch"].get("restricted_actions"),
    json.loads(d)["branch"].get("parent_lsn")))
time.sleep(3)
hpf = pw_of(FK)
ok, data = dselect(hpf, "fork", tries=20, wait=5)
out("fork dataplane: ok=%s data=%s" % (ok, data))
orig = "alice.real" in data
out(">>> FORK-OF-FAILED-BRANCH HOLDS ORIGINAL DATA: %s" % orig)

# ---- 4. DELETE -> recover cycle on failed branch ----
call("DELETE", "/projects/%s/branches/%s" % (PA, FAIL))
out("deleted failed branch")
time.sleep(3)
st, d = call("POST", "/projects/%s/branches/%s/recover" % (PA, FAIL))
out("recover: %s %s" % (st, d[:400]))
if st in (200, 201):
    try:
        rb = json.loads(d)["branch"]
        out("recovered branch ra=%s state=%s" % (rb.get("restricted_actions"), rb.get("current_state")))
        time.sleep(3)
        ok2, data2 = dselect(pw_of(FAIL), "recover", tries=10, wait=5)
        out("recovered dataplane: ok=%s data=%s" % (ok2, data2))
    except Exception as e:
        out("recover parse err: %s" % str(e)[:150])

# ---- cleanup ----
for bid, tag in ((FK, "u12-fork"), (SRC, "u12-src")):
    call("DELETE", "/projects/%s/branches/%s" % (PA, bid))
    out("cleanup %s" % tag)
call("DELETE", "/projects/%s/branches/%s" % (PA, FAIL))
out("cleanup u12-fail (if still alive)")
print("== DONE", flush=True)
