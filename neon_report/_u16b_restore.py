# -*- coding: utf-8 -*-
"""U16B: D1 completion - restore-to-historical endpoint with correct params.
Previous run showed POST /branches/{id}/restore requires source_branch_id.
Goal: is the restore endpoint (semantically == reset_to_parent which is 422-gated
on restricted branches) gated by restricted_actions?
Body candidates:
  {"source_branch_id": <self>, "parent_lsn": <pre-masking LSN>}   (rewind self)
  {"source_branch_id": <self>, "parent_timestamp": ...}
Also fix leftover from u16: set main as default again, delete u16-fail/u16-src.
Zero-destruction: own project, self-made data, all cleaned up.
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
LOG = r"F:\scan\neon_report\_u16b_out.txt"

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


def try_dataplane(bid, table="u16b_pii", retries=2):
    hp, err = pw_of(bid)
    if hp is None:
        return False, "pw_uri:%s" % err
    last = None
    for i in range(retries):
        try:
            c = connect(*hp)
            try:
                rows = query(c, "select * from %s" % table)
                c.close()
                return True, repr(rows)
            except Exception as e:
                last = "sql:%s" % str(e)[:120]
                try:
                    c.close()
                except Exception:
                    pass
        except Exception as e:
            last = "conn:%s" % str(e)[:120]
        time.sleep(3)
    return False, last


def wait_anon(pid, bid, want_kw, tries=30, gap=5):
    for _ in range(tries):
        st, d = call("GET", "/projects/%s/branches/%s/anonymized_status" % (PA, bid))
        low = d.lower()
        if want_kw in low or any(k in low for k in ("fail", "error", "cancelled")):
            return st, d
        time.sleep(gap)
    return st, d


def wait_branch(pid, bid, want="ready", tries=30, gap=4):
    for _ in range(tries):
        st, d = call("GET", "/projects/%s/branches/%s" % (pid, bid))
        if st == 200:
            b = json.loads(d).get("branch", {})
            if b.get("pending_state") == want or (b.get("current_state") == want and not b.get("pending_state")):
                return True, d
        time.sleep(gap)
    return False, d


# ===== stage 0: fix leftover - main back to default, delete u16 leftovers =====
out("=== stage0 leftover fix ===")
st, d = call("POST", "/projects/%s/branches/%s/set_as_default" % (PA, PAMAIN), {})
out("set main default: %s %s" % (st, d[:200]))
time.sleep(3)
st, d = call("GET", "/projects/%s/branches" % PA)
for b in json.loads(d).get("branches", []):
    if b.get("name", "").startswith(("u16-",)):
        st2, d2 = call("DELETE", "/projects/%s/branches/%s" % (PA, b["id"]))
        out("del %s (%s): %s %s" % (b["name"], b["id"], st2, d2[:160]))
        time.sleep(2)

# ===== stage 1: fresh src + data =====
out("=== stage1 src ===")
st, d = call("POST", "/projects/%s/branches" % PA,
             {"branch": {"name": "u16b-src", "parent_id": PAMAIN},
              "endpoints": [{"type": "read_write"}]})
SRC = json.loads(d)["branch"]["id"]
out("src=%s" % SRC)
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
query(conn, "create table if not exists u16b_pii(id int, email text, secret text)")
query(conn, "delete from u16b_pii")
query(conn, "insert into u16b_pii values (1,'alice.real@victimcorp.com','ssn-111'),(2,'bob.ceo@victimcorp.com','ssn-222')")
out("src seeded: %s" % repr(query(conn, "select * from u16b_pii")))
conn.close()

# ===== stage 2: successful anonymized branch =====
out("=== stage2 anon ok ===")
st, d = call("POST", "/projects/%s/branch_anonymized" % PA, {
    "branch_create": {"branch": {"name": "u16b-ok", "parent_id": SRC},
                      "endpoints": [{"type": "read_write"}]},
    "masking_rules": [{
        "database_name": "neondb", "schema_name": "public",
        "table_name": "u16b_pii", "column_name": "email",
        "masking_function": "anon.fake_email()"}],
    "start_anonymization": True,
})
OKB = json.loads(d)["branch"]["id"]
out("u16b-ok id=%s plsn=%s" % (OKB, json.loads(d)["branch"].get("parent_lsn")))
st, d = wait_anon(PA, OKB, "anonymized")
out("anon done: %s %s" % (st, d[:180]))
st, d = call("GET", "/projects/%s/branches/%s" % (PA, OKB))
bj = json.loads(d).get("branch", {})
PLSN = bj.get("parent_lsn")
out("ra=%s plsn=%s" % (bj.get("restricted_actions"), PLSN))

# ===== stage 3: restore endpoint probes =====
out("=== stage3 restore probes ===")
PROBES = [
    ("self+plsn", {"source_branch_id": OKB, "parent_lsn": PLSN}),
    ("self+ts", {"source_branch_id": OKB, "parent_timestamp": bj.get("parent_timestamp")}),
]
for tag, body in PROBES:
    st, d = call("POST", "/projects/%s/branches/%s/restore" % (PA, OKB), body)
    out("restore %s: %s %s" % (tag, st, d[:400]))
    if st in (400, 422):
        try:
            e = json.loads(d)
            out("  err code=%s msg=%s" % (e.get("code"), e.get("message", "")[:300]))
        except Exception:
            pass
    if st in (200, 201, 202):
        # restore is async; watch branch for restore_status / timeline change
        for i in range(20):
            time.sleep(5)
            st2, d2 = call("GET", "/projects/%s/branches/%s" % (PA, OKB))
            b2 = json.loads(d2).get("branch", {})
            rs = b2.get("restore_status")
            out("t+%ds restore_status=%s state=%s/%s" % (
                (i + 1) * 5, rs, b2.get("current_state"), b2.get("pending_state")))
            if rs == "done" or (rs is None and not b2.get("pending_state")):
                break
        okd, r = try_dataplane(OKB, "u16b_pii", retries=6)
        raw = "alice.real" in r
        out("dataplane after restore: ok=%s RAW=%s %s" % (okd, raw, r[:220]))
        st2, d2 = call("GET", "/projects/%s/branches/%s" % (PA, OKB))
        out("final ra=%s state=%s" % (
            json.loads(d2).get("branch", {}).get("restricted_actions"),
            json.loads(d2).get("branch", {}).get("current_state")))
        break

# ===== stage 4: control - reset_to_parent still gated (same semantics) =====
out("=== stage4 reset_to_parent control ===")
st, d = call("POST", "/projects/%s/branches/%s/reset_to_parent" % (PA, OKB))
out("reset_to_parent: %s %s" % (st, d[:250]))

# ===== stage 5: cleanup =====
out("=== stage5 cleanup ===")
st, d = call("DELETE", "/projects/%s/branches/%s" % (PA, OKB))
out("del u16b-ok: %s %s" % (st, d[:150]))
time.sleep(2)
st, d = call("DELETE", "/projects/%s/branches/%s" % (PA, SRC))
out("del src: %s %s" % (st, d[:150]))
st, d = call("GET", "/projects/%s/branches" % PA)
out("FINAL:")
for b in json.loads(d).get("branches", []):
    out("  %-24s %s default=%s" % (b.get("name"), b.get("id"), b.get("default")))
print("== DONE", flush=True)
