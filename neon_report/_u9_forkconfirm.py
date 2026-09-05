# -*- coding: utf-8 -*-
"""Confirm time-independence: wait 3 min after anonymization, fork anon at
parent_lsn=fork point -> original data must still be there. Print child
restricted_actions. Also try branch_anonymized with parent_lsn (masked path)."""
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
LOG = r"F:\scan\neon_report\_u9_out.txt"

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
            time.sleep(wait)
    return None


# cleanup u9 leftovers
st, d = call("GET", "/projects/%s/branches" % PA)
for b in json.loads(d).get("branches", []):
    if b.get("name", "").startswith("u9-"):
        call("DELETE", "/projects/%s/branches/%s" % (PA, b["id"]))
        out("cleaned %s" % b["name"])

# 1. src + data
st, d = call("POST", "/projects/%s/branches" % PA,
             {"branch": {"name": "u9-src", "parent_id": PAMAIN},
              "endpoints": [{"type": "read_write"}]})
SRC = json.loads(d)["branch"]["id"]
conn = connect_wait(SRC)
time.sleep(2)
exec_(conn, "create table u9_pii(id int, email text, secret text)")
exec_(conn, "insert into u9_pii values (1,'victim1@corp.example','ssn-AAA'),(2,'victim2@corp.example','ssn-BBB')")
out("src: %s" % repr(query(conn, "select * from u9_pii")))
conn.close()

# 2. anon
st, d = call("POST", "/projects/%s/branch_anonymized" % PA, {
    "branch_create": {"branch": {"name": "u9-anon", "parent_id": SRC},
                      "endpoints": [{"type": "read_write"}]},
    "masking_rules": [{
        "database_name": "neondb", "schema_name": "public",
        "table_name": "u9_pii", "column_name": "email",
        "masking_function": "anon.fake_email()"
    }],
    "start_anonymization": True,
})
j = json.loads(d)
ANON = j["branch"]["id"]
LSN0 = j["branch"].get("parent_lsn")
out("anon=%s parent_lsn=%s" % (ANON, LSN0))
conn2 = connect_wait(ANON)
out("anon rows (masked): %s" % repr(query(conn2, "select * from u9_pii")))
conn2.close()

# 3. WAIT 180s -> time independence
out("waiting 180s ...", )
time.sleep(180)
out("wait done")

# 4. fork anon at fork-point LSN now
st, d = call("POST", "/projects/%s/branches" % PA,
             {"branch": {"name": "u9-fork", "parent_id": ANON, "parent_lsn": LSN0},
              "endpoints": [{"type": "read_write"}]})
out("fork create: %s %s" % (st, d[:500]))
try:
    jf = json.loads(d)
    FK = jf["branch"]["id"]
    out("fork restricted_actions: %s" % jf["branch"].get("restricted_actions"))
    conn3 = connect_wait(FK, tries=25, wait=6)
    if conn3:
        rows = query(conn3, "select * from u9_pii")
        out("fork rows after 3min: %s" % repr(rows))
        orig = any("victim" in str(r[1]) for r in rows)
        out(">>> ORIGINAL DATA RECOVERED AFTER 3 MIN: %s" % orig)
        conn3.close()
    call("DELETE", "/projects/%s/branches/%s" % (PA, FK))
except Exception as e:
    out("fork err: %s %s" % (type(e).__name__, str(e)[:150]))

# 5. branch_anonymized path with parent_lsn (masked-create on anon history)
st, d = call("POST", "/projects/%s/branch_anonymized" % PA, {
    "branch_create": {"branch": {"name": "u9-anon2", "parent_id": ANON,
                                 "parent_lsn": LSN0},
                      "endpoints": [{"type": "read_write"}]},
    "masking_rules": [{
        "database_name": "neondb", "schema_name": "public",
        "table_name": "u9_pii", "column_name": "email",
        "masking_function": "anon.fake_email()"
    }],
    "start_anonymization": False,
})
out("anon2(hist) create: %s %s" % (st, d[:300]))
try:
    ja = json.loads(d)
    A2 = ja["branch"]["id"]
    conn4 = connect_wait(A2, tries=25, wait=6)
    if conn4:
        out("anon2 rows: %s" % repr(query(conn4, "select * from u9_pii")))
        conn4.close()
    call("DELETE", "/projects/%s/branches/%s" % (PA, A2))
except Exception as e:
    out("anon2 err: %s" % str(e)[:150])

# cleanup
for bid, tag in ((ANON, "u9-anon"), (SRC, "u9-src")):
    call("DELETE", "/projects/%s/branches/%s" % (PA, bid))
    out("cleanup %s" % tag)
print("== DONE", flush=True)
