# -*- coding: utf-8 -*-
"""ANGLE-1+2: anonymization job FAILURE state machine.
Does restricted_actions get released when the masking job fails, while the
data stays fully unmasked (PG single-statement UPDATE failure = 0 rows changed)?
Variants: (a) nonexistent column (b) nonexistent function (c) type mismatch.
During each run we also poll the data plane every 5s to catch the live window
(angle-2: connect while job still running).
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
LOG = r"F:\scan\neon_report\_u11_out.txt"

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
        return None, d[:120]
    from urllib.parse import urlsplit
    u = urlsplit(json.loads(d)["uri"])
    return (u.hostname, u.username, u.password), None


def try_dataplane(bid, tag):
    """One-shot data plane connect+select; returns (ok, rows) or (False, err)."""
    hp, err = pw_of(bid)
    if hp is None:
        return False, "pw_uri:%s" % err
    try:
        c = connect(*hp)
    except Exception as e:
        return False, "conn:%s" % str(e)[:100]
    try:
        rows = query(c, "select * from u11_pii")
        c.close()
        return True, repr(rows)
    except Exception as e:
        try:
            c.close()
        except Exception:
            pass
        return False, "sql:%s" % str(e)[:100]


# ---- cleanup leftovers ----
st, d = call("GET", "/projects/%s/branches" % PA)
for b in json.loads(d).get("branches", []):
    if b.get("name", "").startswith("u11-"):
        call("DELETE", "/projects/%s/branches/%s" % (PA, b["id"]))
        out("cleaned %s" % b["name"])
time.sleep(2)

# ---- 1. src + data ----
st, d = call("POST", "/projects/%s/branches" % PA,
             {"branch": {"name": "u11-src", "parent_id": PAMAIN},
              "endpoints": [{"type": "read_write"}]})
SRC = json.loads(d)["branch"]["id"]
out("src=%s create:%s" % (SRC, st))
hp = None
for i in range(15):
    hp, err = pw_of(SRC)
    if hp:
        break
    time.sleep(4)
conn = None
for i in range(15):
    try:
        conn = connect(*hp)
        break
    except Exception as e:
        time.sleep(4)
query(conn, "create table if not exists u11_pii(id int, email text, secret text)")
query(conn, "delete from u11_pii")
query(conn, "insert into u11_pii values (1,'alice.real@victimcorp.com','ssn-111'),(2,'bob.ceo@victimcorp.com','ssn-222'),(3,'carol.vp@victimcorp.com','ssn-333')")
out("src seeded: %s" % repr(query(conn, "select * from u11_pii")))
conn.close()

# ---- 2. failure variants ----
VARIANTS = [
    ("u11-failcol", [{
        "database_name": "neondb", "schema_name": "public",
        "table_name": "u11_pii", "column_name": "no_such_column",
        "masking_function": "anon.fake_email()"}]),
    ("u11-failfn", [{
        "database_name": "neondb", "schema_name": "public",
        "table_name": "u11_pii", "column_name": "email",
        "masking_function": "anon.no_such_fn()"}]),
    ("u11-failtype", [{
        "database_name": "neondb", "schema_name": "public",
        "table_name": "u11_pii", "column_name": "id",
        "masking_function": "anon.fake_email()"}]),
]

for name, rules in VARIANTS:
    out("\n=== variant %s ===" % name)
    st, d = call("POST", "/projects/%s/branch_anonymized" % PA, {
        "branch_create": {"branch": {"name": name, "parent_id": SRC},
                          "endpoints": [{"type": "read_write"}]},
        "masking_rules": rules,
        "start_anonymization": True,
    })
    out("create: %s %s" % (st, d[:400]))
    if st not in (200, 201):
        out("!! create rejected at API layer (validation upstream) -> no fail state reachable")
        continue
    j = json.loads(d)
    ANON = j["branch"]["id"]
    out("anon id=%s ra=%s" % (ANON, j["branch"].get("restricted_actions")))

    # poll status + data plane every 5s for up to 150s
    saw_original = False
    status_seen = {}
    t0 = time.time()
    while time.time() - t0 < 150:
        time.sleep(5)
        st2, d2 = call("GET", "/projects/%s/branches/%s/anonymized_status" % (PA, ANON))
        snippet = d2[:250]
        status_seen[st2] = snippet
        ok, r = try_dataplane(ANON, name)
        if ok:
            raw = "alice.real" in r or "victimcorp" in r
            out("t+%.0fs status(%s) %s | dataplane OK rows=%s ORIGINAL=%s" %
                (time.time() - t0, st2, snippet.replace("\n", " "), r, raw))
            if raw:
                saw_original = True
        else:
            out("t+%.0fs status(%s) %s | dataplane BLOCKED (%s)" %
                (time.time() - t0, st2, snippet.replace("\n", " "), r[:80]))
        # terminal conditions
        if "anonymized" in d2 and ("true" in d2.lower() or "completed" in d2.lower()):
            # state word anonymized might be the final one; keep polling a bit
            pass
        if st2 == 404 or '"error"' in d2 and "not found" in d2:
            out("branch gone?"); break
        # break when status shows a terminal failure keyword
        low = d2.lower()
        if any(k in low for k in ("fail", "error", "cancelled", "canceled")) and "not found" not in low:
            # keep 2 more rounds to observe if ra released then stop
            time.sleep(10)
            st3, d3 = call("GET", "/projects/%s/branches/%s" % (PA, ANON))
            out("terminal: GET branch %s %s" % (st3, d3[:500]))
            break

    out("variant %s: ORIGINAL DATA READABLE VIA DATA PLANE = %s" % (name, saw_original))

    # ---- post-mortem probes ----
    st, d = call("GET", "/projects/%s/branches/%s" % (PA, ANON))
    out("postmortem GET branch: %s %s" % (st, d[:600]))
    try:
        bj = json.loads(d)["branch"]
        out("postmortem state=%s ra=%s anon_status=%s" % (
            bj.get("state"), bj.get("restricted_actions"),
            bj.get("anonymized_status") or bj.get("anonymization_state")))
    except Exception:
        pass
    st, d = call("POST", "/projects/%s/branches/%s/reset_to_parent" % (PA, ANON))
    out("postmortem reset_to_parent: %s %s" % (st, d[:250]))
    st, d = call("POST", "/projects/%s/branches" % PA,
                 {"branch": {"name": name + "-fork", "parent_id": ANON}})
    out("postmortem fork: %s %s" % (st, d[:250]))
    if st in (200, 201):
        call("DELETE", "/projects/%s/branches/%s" % (PA, json.loads(d)["branch"]["id"]))
    # last data plane read
    ok, r = try_dataplane(ANON, name)
    out("postmortem dataplane: ok=%s %s" % (ok, r[:200]))
    # cleanup
    st, d = call("DELETE", "/projects/%s/branches/%s" % (PA, ANON))
    out("cleanup %s: %s %s" % (name, st, d[:150]))

# ---- cleanup src ----
call("DELETE", "/projects/%s/branches/%s" % (PA, SRC))
out("cleanup src")
print("== DONE", flush=True)
