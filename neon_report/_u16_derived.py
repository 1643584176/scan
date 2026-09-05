# -*- coding: utf-8 -*-
"""DERIVED SURFACE: restricted_actions coverage consistency audit.
Question: the anonymized-branch lock (restore/delete-rw-endpoint/connect-to-endpoints)
is enforced on reset_to_parent (422) and data plane (57P03). Are OTHER endpoints that
can rewind a timeline / reach raw data equally gated?

 D1 restore-to-historical-state endpoint  POST /branches/{id}/restore   (rewind anon branch to pre-masking LSN?)
 D2 snapshot channel on failed branch      snapshot create + snapshot restore -> new branch (raw data, no fork)
 D3 masking-rules PATCH + re-anonymize     initialized branch (raw data, dataplane disabled) -> rules cleared ->
                                           anonymize succeeds -> connect-to-endpoints released -> raw data READ
                                           directly on the SAME branch (no fork at all)
 D4 quick probes: PATCH branch attrs / set_as_default on restricted branch

Zero-destruction: self-made data, own project, branches/snapshots deleted at the end.
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
LOG = r"F:\scan\neon_report\_u16_out.txt"

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


def try_dataplane(bid, table="u16_pii", retries=1):
    """Returns (ok, payload) - one-shot connect + select."""
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
    """Poll anonymized_status until a terminal keyword appears."""
    for _ in range(tries):
        st, d = call("GET", "/projects/%s/branches/%s/anonymized_status" % (PA, bid))
        low = d.lower()
        if want_kw in low:
            return st, d
        if any(k in low for k in ("fail", "error", "cancelled")):
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


# ================= cleanup leftovers =================
st, d = call("GET", "/projects/%s/branches" % PA)
for b in json.loads(d).get("branches", []):
    if b.get("name", "").startswith(("u16-",)):
        call("DELETE", "/projects/%s/branches/%s" % (PA, b["id"]))
        out("cleaned branch %s" % b["name"])
st, d = call("GET", "/projects/%s/snapshots" % PA)
for s in json.loads(d).get("snapshots", []):
    if s.get("name", "").startswith("u16-"):
        call("DELETE", "/projects/%s/snapshots/%s" % (PA, s["id"]))
        out("cleaned snapshot %s" % s["name"])
time.sleep(2)

# ================= src branch + seed =================
st, d = call("POST", "/projects/%s/branches" % PA,
             {"branch": {"name": "u16-src", "parent_id": PAMAIN},
              "endpoints": [{"type": "read_write"}]})
SRC = json.loads(d)["branch"]["id"]
out("src=%s create:%s" % (SRC, st))
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
query(conn, "create table if not exists u16_pii(id int, email text, secret text)")
query(conn, "delete from u16_pii")
query(conn, "insert into u16_pii values (1,'alice.real@victimcorp.com','ssn-111'),(2,'bob.ceo@victimcorp.com','ssn-222'),(3,'carol.vp@victimcorp.com','ssn-333')")
out("src seeded: %s" % repr(query(conn, "select * from u16_pii")))
conn.close()

KEEP = []          # ids to delete at the end (branches)
KSNAP = []         # snapshot ids


def mk_anon(name, rules, start=True, src=SRC):
    """Create anonymized branch; returns (bid, create_json)."""
    st, d = call("POST", "/projects/%s/branch_anonymized" % PA, {
        "branch_create": {"branch": {"name": name, "parent_id": src},
                          "endpoints": [{"type": "read_write"}]},
        "masking_rules": rules,
        "start_anonymization": start,
    })
    out("mk_anon %s: %s %s" % (name, st, d[:300]))
    if st not in (200, 201):
        return None, None
    bj = json.loads(d)["branch"]
    KEEP.append(bj["id"])
    return bj["id"], bj


# ================= D1: restore-to-historical endpoint on an anonymized branch =================
out("\n===== D1 restore-to-historical POST /branches/{id}/restore =====")
ok1, bj1 = mk_anon("u16-ok", [{
    "database_name": "neondb", "schema_name": "public",
    "table_name": "u16_pii", "column_name": "email",
    "masking_function": "anon.fake_email()"}])
if ok1:
    st, d = wait_anon(PA, ok1, "anonymized")
    out("D1 anon done: %s %s" % (st, d[:200]))
    # restore probe: empty body first to learn the parameter shape
    st, d = call("POST", "/projects/%s/branches/%s/restore" % (PA, ok1), {})
    out("D1 restore empty-body: %s %s" % (st, d[:400]))
    if st in (400, 422):
        try:
            e = json.loads(d)
            out("D1 restore err code=%s msg=%s" % (e.get("code"), e.get("message", "")[:300]))
        except Exception:
            pass
    # try parent_lsn of the anonymized branch (pre-masking fork point)
    st, d = call("GET", "/projects/%s/branches/%s" % (PA, ok1))
    bj = json.loads(d).get("branch", {})
    plsn = bj.get("parent_lsn")
    out("D1 anon branch parent_lsn=%s" % plsn)
    if plsn:
        st, d = call("POST", "/projects/%s/branches/%s/restore" % (PA, ok1),
                     {"parent_lsn": plsn})
        out("D1 restore parent_lsn: %s %s" % (st, d[:400]))
        if st in (400, 422):
            try:
                e = json.loads(d)
                out("D1 restore plsn err code=%s msg=%s" % (e.get("code"), e.get("message", "")[:300]))
            except Exception:
                pass
    # data plane still masked on anon branch (control)
    okd, r = try_dataplane(ok1)
    out("D1 anon dataplane (expect masked): ok=%s %s" % (okd, r[:200]))

# ================= D2: snapshot channel on failed branch =================
out("\n===== D2 snapshot channel (failed branch holds RAW data) =====")
fail2, _ = mk_anon("u16-fail", [{
    "database_name": "neondb", "schema_name": "public",
    "table_name": "u16_pii", "column_name": "email",
    "masking_function": "anon.no_such_fn()"}])
if fail2:
    st, d = wait_anon(PA, fail2, "fail")
    out("D2 fail state: %s %s" % (st, d[:250]))
    st, d = call("POST", "/projects/%s/branches/%s/snapshot?name=u16-fail-snap" % (PA, fail2))
    out("D2 snapshot create on failed br: %s %s" % (st, d[:350]))
    sid = None
    if st in (200, 201):
        sid = json.loads(d).get("snapshot", {}).get("id")
        KSNAP.append(sid)
        # wait listed
        for _ in range(15):
            st2, d2 = call("GET", "/projects/%s/snapshots" % PA)
            hit = [s for s in json.loads(d2).get("snapshots", []) if s.get("id") == sid]
            if hit:
                out("D2 snapshot listed status=%s" % hit[0].get("status"))
                break
            time.sleep(2)
    if sid:
        st, d = call("POST", "/projects/%s/snapshots/%s/restore" % (PA, sid), {})
        out("D2 snapshot restore(no target): %s %s" % (st, d[:350]))
        if st in (200, 201):
            brr = json.loads(d).get("branch", {})
            rid = brr.get("id")
            KEEP.append(rid)
            out("D2 restored branch id=%s restore_status=%s" % (rid, brr.get("restore_status")))
            okw, dw = wait_branch(PA, rid)
            out("D2 restored branch ready: %s" % okw)
            # data plane on restored branch
            okd, r = try_dataplane(rid, "u16_pii", retries=8)
            raw = "alice.real" in r
            out("D2 restored-branch dataplane: ok=%s RAW=%s %s" % (okd, raw, r[:220]))
            st, d = call("GET", "/projects/%s/branches/%s" % (PA, rid))
            bj = json.loads(d).get("branch", {})
            out("D2 restored branch ra=%s state=%s" % (bj.get("restricted_actions"), bj.get("current_state")))

# ================= D3: PATCH masking_rules clear + anonymize -> dataplane release =================
out("\n===== D3 masking_rules PATCH + anonymize on initialized (raw) branch =====")
init3, bj3 = mk_anon("u16-init", [{
    "database_name": "neondb", "schema_name": "public",
    "table_name": "u16_pii", "column_name": "email",
    "masking_function": "anon.fake_email()"}], start=False)
if init3:
    okd, r = try_dataplane(init3)
    out("D3 init dataplane (expect 57P03): ok=%s %s" % (okd, r[:160]))
    st, d = call("GET", "/projects/%s/branches/%s/masking_rules" % (PA, init3))
    out("D3 GET masking_rules: %s %s" % (st, d[:300]))
    st, d = call("PATCH", "/projects/%s/branches/%s/masking_rules" % (PA, init3),
                 {"masking_rules": []})
    out("D3 PATCH masking_rules=[]: %s %s" % (st, d[:300]))
    st, d = call("GET", "/projects/%s/branches/%s/masking_rules" % (PA, init3))
    out("D3 GET masking_rules after: %s %s" % (st, d[:300]))
    st, d = call("POST", "/projects/%s/branches/%s/anonymize" % (PA, init3), {})
    out("D3 POST anonymize: %s %s" % (st, d[:250]))
    st, d = wait_anon(PA, init3, "anonymized", tries=24)
    out("D3 anon status terminal: %s %s" % (st, d[:250]))
    # if state reached anonymized -> connect-to-endpoints should be released -> RAW data?
    okd, r = try_dataplane(init3, retries=4)
    raw = "alice.real" in r
    out("D3 dataplane after re-anonymize(no rules): ok=%s RAW=%s %s" % (okd, raw, r[:220]))
    st, d = call("GET", "/projects/%s/branches/%s" % (PA, init3))
    bj = json.loads(d).get("branch", {})
    out("D3 branch ra=%s" % bj.get("restricted_actions"))

# ================= D4: quick probes on restricted branches =================
out("\n===== D4 quick probes =====")
for bid, tag in ((ok1, "ok"), (fail2, "fail")):
    if not bid:
        continue
    st, d = call("PATCH", "/projects/%s/branches/%s" % (PA, bid),
                 {"branch": {"name": tag + "-renamed"}})
    out("D4 PATCH branch name on %s: %s %s" % (tag, st, d[:200]))
    st, d = call("POST", "/projects/%s/branches/%s/set_as_default" % (PA, bid), {})
    out("D4 set_as_default on %s: %s %s" % (tag, st, d[:200]))
    # restore back name for tidiness (best effort)
    call("PATCH", "/projects/%s/branches/%s" % (PA, bid),
         {"branch": {"name": "u16-" + tag}})

# ================= cleanup =================
out("\n===== cleanup =====")
for s in KSNAP:
    st, d = call("DELETE", "/projects/%s/snapshots/%s" % (PA, s))
    out("del snapshot %s: %s" % (s, st))
for bid in reversed(KEEP):
    st, d = call("DELETE", "/projects/%s/branches/%s" % (PA, bid))
    out("del branch %s: %s %s" % (bid, st, d[:120]))
    time.sleep(2)
call("DELETE", "/projects/%s/branches/%s" % (PA, SRC))
out("del src")
st, d = call("GET", "/projects/%s/branches" % PA)
out("FINAL:")
for b in json.loads(d).get("branches", []):
    out("  %-24s %s" % (b.get("name"), b.get("id")))
print("== DONE", flush=True)
