# -*- coding: utf-8 -*-
"""W3: schema-only branch (preview) data-isolation black-box (console-stage).
Docs: POST /projects/{project_id}/branches with branch.init_source="schema-only"
=> copies ONLY schema, "no actual data". Root cause is unrelated to the
anonymized-branch restricted_actions chain.

Attack model: schema-only branch must never expose parent DATA through ANY
read path. Probes:
  S0 baseline branches (cleanup ledger)
  S1 src branch w3src-* from main + endpoint; create table so_probe; insert 100
     self-marked rows; record parent_lsn_pre / parent_lsn_post
  S2 create schema-only branch w3so-* from src (init_source=schema-only);
     inspect create response (endpoints/ops/echoed fields), wait ready
  S3 connect to w3so compute: to_regclass / count(*) / writability
  S4 leak probes:
     P1 full child branch of w3so        -> count(*) on so_probe (KEY)
     P2 PITR child of w3so with
        parent_lsn = w3so.parent_lsn     -> count(*) (ancestral pages?)
     P3 restore w3so to src head lsn     -> count(*) (if restore enabled)
     P4 schema-only create WITH
        parent_lsn = parent_lsn_post     -> count(*) direct
  S5 cleanup: DELETE all w3-* branches
Self-created data only; every request carries X-Bug-Bounty: xxbo.
"""
import json
import ssl
import time
import uuid
import http.client
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
HB = {"X-Bug-Bounty": "xxbo", "Content-Type": "application/json"}
PA = "orange-sun-90493739"          # project A (sec-i-1, our own staging project)
PAMAIN = "br-wandering-field-w2ob6mpn"
TAG = "w3" + uuid.uuid4().hex[:4]
LOG = r"F:\scan\neon_report\_w3_out.txt"

with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]


def out(s):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), s)
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def call(method, path, body=None, timeout=45, tries=3):
    last = (None, "")
    for _ in range(tries):
        try:
            ctx = ssl.create_default_context()
            conn = http.client.HTTPSConnection(API_HOST, timeout=timeout, context=ctx)
            payload = json.dumps(body) if body is not None else None
            conn.request(method, API_BASE + path, body=payload,
                         headers=dict(HB, Authorization="Bearer " + APIKEY))
            resp = conn.getresponse()
            data = resp.read().decode("utf-8", "replace")
            conn.close()
            return resp.status, data
        except Exception as e:
            last = (None, str(e)[:120])
            time.sleep(2)
    return last


def jget(raw, *keys):
    try:
        d = json.loads(raw)
        for k in keys:
            d = d[k]
        return d
    except Exception:
        return None


def wait_branch(bid, want="ready", tries=40, gap=3):
    for _ in range(tries):
        st, raw = call("GET", "/projects/%s/branches/%s" % (PA, bid))
        if st == 200:
            b = jget(raw, "branch") or {}
            if b.get("pending_state") == want or (
                    b.get("current_state") == want and b.get("pending_state") is None):
                return True, b
        time.sleep(gap)
    return False, {}


def ensure_endpoint(bid, create_body=None):
    """Return endpoint host for a branch, creating an endpoint if none exists."""
    # 1) endpoint may already exist
    st, raw = call("GET", "/projects/%s/branches/%s/endpoints" % (PA, bid))
    eps = jget(raw, "endpoints") if st == 200 else None
    if isinstance(eps, list) and eps:
        ep = eps[0]
        if ep.get("host"):
            return ep["host"], "existing"
    # 2) create read_write endpoint (route: POST /projects/{pid}/endpoints)
    if create_body is None:
        create_body = {"endpoint": {"branch_id": bid, "type": "read_write"}}
    st, raw = call("POST", "/projects/%s/endpoints" % PA, create_body)
    out("S  endpoint create %s -> %s %s" % (bid, st, raw[:180]))
    for _ in range(40):
        time.sleep(3)
        st, raw = call("GET", "/projects/%s/branches/%s/endpoints" % (PA, bid))
        eps = jget(raw, "endpoints") if st == 200 else None
        if isinstance(eps, list) and eps:
            ep = eps[0]
            if ep.get("host"):
                return ep["host"], "created"
    return None, "no-endpoint"


def branch_uri(bid):
    st, raw = call("GET", "/projects/%s/connection_uri?database_name=neondb"
                          "&role_name=neondb_owner&branch_id=%s" % (PA, bid))
    uri = jget(raw, "uri")
    if not uri:
        return None
    parts = urlsplit(uri)
    q = [(k, v) for k, v in parse_qsl(parts.query) if k != "channel_binding"]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(q), parts.fragment))


def db_q(uri, sql, retries=6):
    import psycopg
    last = None
    for _ in range(retries):
        try:
            with psycopg.connect(uri, connect_timeout=20) as conn:
                conn.autocommit = True
                with conn.cursor() as cur:
                    cur.execute(sql)
                    if cur.description:
                        return ("OK", cur.fetchall())
                    return ("OK", None)
        except Exception as e:
            last = e
            time.sleep(5)
    return ("ERR", str(last)[:200])


def create_branch(name, parent_id, extra=None, with_ep=False):
    branch = {"name": name, "parent_id": parent_id}
    if extra:
        branch.update(extra)
    body = {"branch": branch}
    if with_ep:
        body["endpoints"] = [{"type": "read_write"}]
    st, raw = call("POST", "/projects/%s/branches" % PA, body)
    bid = jget(raw, "branch", "id")
    if st in (200, 201) and bid:
        out("S  create %-18s -> 200 id=%s  resp(branch): %s" %
            (name, bid, json.dumps(jget(raw, "branch") or {})[:600]))
    else:
        out("S  create %-18s -> %s %s" % (name, st, raw[:300]))
    return st, bid, raw


def main():
    out("== W3 schema-only isolation  tag=%s ==" % TAG)
    created = []   # (name, bid)

    # ---------- S1 src branch + data ----------
    st, src_id, raw = create_branch("w3src-%s" % TAG, PAMAIN)
    if not src_id:
        out("S1 FAILED to create src branch")
        return
    created.append(("w3src-%s" % TAG, src_id))
    ok, b = wait_branch(src_id)
    out("S1 src ready: %s" % (ok,))
    host, how = ensure_endpoint(src_id)
    out("S1 src endpoint host=%s (%s)" % (host, how))
    uri = branch_uri(src_id)
    out("S1 src uri got: %s" % bool(uri))
    if not uri:
        out("S1 ABORT: no uri")
        return
    r = db_q(uri, "SELECT pg_current_wal_lsn()")
    lsn_pre = r[1][0][0] if r[0] == "OK" else None
    r = db_q(uri, "CREATE TABLE public.so_probe (id serial PRIMARY KEY, secret text)")
    out("S1 create table: %s" % (r[0],))
    vals = ",".join("('W3PII-%d-%s')" % (i, uuid.uuid4().hex[:12])
                    for i in range(100))
    r = db_q(uri, "INSERT INTO public.so_probe (secret) VALUES %s" % vals)
    out("S1 insert 100: %s" % (r[0],))
    r = db_q(uri, "SELECT pg_current_wal_lsn()")
    lsn_post = r[1][0][0] if r[0] == "OK" else None
    r = db_q(uri, "SELECT count(*) FROM public.so_probe")
    out("S1 src count: %s %s  lsn_pre=%s lsn_post=%s" % (r[0], r[1], lsn_pre, lsn_post))

    # ---------- S2 schema-only branch ----------
    st, so_id, raw = create_branch("w3so-%s" % TAG, src_id,
                                   extra={"init_source": "schema-only"}, with_ep=True)
    if not so_id:
        out("S2 schema-only CREATE FAILED (%s %s) -> try flat/alt spellings" % (st, raw[:200]))
        for alt in [{"branch": {"name": "w3so-%s" % TAG, "parent_id": src_id,
                                "init_source": "schema_only"}},
                    {"name": "w3so-%s" % TAG, "parent_id": src_id,
                     "init_source": "schema-only"},
                    {"branch": {"name": "w3so-%s" % TAG, "parent_id": src_id},
                     "init_source": "schema-only"}]:
            st2, raw2 = call("POST", "/projects/%s/branches" % PA, alt)
            out("S2 alt %s -> %s %s" % (json.dumps(alt)[:120], st2, raw2[:250]))
            bid2 = jget(raw2, "branch", "id") if st2 in (200, 201) else None
            if bid2:
                so_id = bid2
                break
        if not so_id:
            out("S2 GIVE UP: schema-only unavailable")
            for _, bid in created:
                call("DELETE", "/projects/%s/branches/%s" % (PA, bid))
            return
    created.append(("w3so-%s" % TAG, so_id))
    ok, b = wait_branch(so_id)
    so_parent_lsn = b.get("parent_lsn")
    out("S2 so ready=%s  parent_lsn=%s  branch: %s" %
        (ok, so_parent_lsn, json.dumps(b)[:400]))

    # ---------- S3 connect to schema-only branch ----------
    host2, how2 = ensure_endpoint(so_id)
    out("S3 so endpoint host=%s (%s)" % (host2, how2))
    uri2 = branch_uri(so_id)
    out("S3 so uri got: %s" % bool(uri2))
    if not uri2:
        out("S3 ABORT: no so uri")
    else:
        r = db_q(uri2, "SELECT to_regclass('public.so_probe')")
        out("S3 so to_regclass: %s %s" % (r[0], r[1]))
        r = db_q(uri2, "SELECT count(*) FROM public.so_probe")
        out("S3 so count: %s %s" % (r[0], r[1]))
        r = db_q(uri2, "INSERT INTO public.so_probe (secret) VALUES ('W3SO-write-ok') "
                       "RETURNING id")
        out("S3 so writable insert: %s %s" % (r[0], r[1]))
        if r[0] == "OK":
            db_q(uri2, "DELETE FROM public.so_probe WHERE secret='W3SO-write-ok'")
            out("S3 so cleanup insert: done")
        # logical footprint: hidden data may still be physically present
        st, raw = call("GET", "/projects/%s/branches/%s" % (PA, so_id))
        if st == 200:
            b2 = jget(raw, "branch") or {}
            out("S3 so detail: logical_size=%s physical_size=%s data_size=%s" %
                (b2.get("logical_size"), b2.get("physical_size"),
                 b2.get("data_size")))

    # ---------- S4 leak probes ----------
    # P1: full child of schema-only branch
    st, ch_id, raw = create_branch("w3ch-%s" % TAG, so_id, with_ep=True)
    if ch_id:
        created.append(("w3ch-%s" % TAG, ch_id))
        wait_branch(ch_id)
        host3, _ = ensure_endpoint(ch_id)
        uri3 = branch_uri(ch_id)
        r = db_q(uri3, "SELECT count(*) FROM public.so_probe") if uri3 else ("NO-URI", None)
        out("P1 child-of-so count: %s %s" % (r[0], r[1]))

    # P2: PITR child of schema-only branch anchored at so.parent_lsn
    if so_parent_lsn:
        st, p2_id, raw = create_branch("w3pitr-%s" % TAG, so_id,
                                       extra={"parent_lsn": so_parent_lsn}, with_ep=True)
        if p2_id:
            created.append(("w3pitr-%s" % TAG, p2_id))
            wait_branch(p2_id)
            host4, _ = ensure_endpoint(p2_id)
            uri4 = branch_uri(p2_id)
            r = db_q(uri4, "SELECT count(*) FROM public.so_probe") if uri4 else ("NO-URI", None)
            out("P2 pitr-child@so.parent_lsn count: %s %s" % (r[0], r[1]))
        else:
            out("P2 create FAILED: %s %s" % (st, raw[:250]))

    # P3: restore schema-only branch back toward src head (if restore enabled)
    if lsn_post:
        st, raw = call("POST", "/projects/%s/branches/%s/restore" % (PA, so_id),
                       {"parent_lsn": lsn_post})
        out("P3 restore so<-src-head: %s %s" % (st, raw[:250]))

    # P4: schema-only create + parent_lsn (combine) directly from src
    st, p4_id, raw = create_branch("w3cob-%s" % TAG, src_id,
                                   extra={"init_source": "schema-only",
                                          "parent_lsn": lsn_post}, with_ep=True)
    if p4_id:
        created.append(("w3cob-%s" % TAG, p4_id))
        wait_branch(p4_id)
        host5, _ = ensure_endpoint(p4_id)
        uri5 = branch_uri(p4_id)
        r = db_q(uri5, "SELECT count(*) FROM public.so_probe") if uri5 else ("NO-URI", None)
        out("P4 schema-only+lsn count: %s %s" % (r[0], r[1]))
    else:
        out("P4 create FAILED: %s %s" % (st, raw[:250]))

    # ---------- S5 cleanup ----------
    out("S5 cleanup %d branches" % len(created))
    for name, bid in reversed(created):
        st, raw = call("DELETE", "/projects/%s/branches/%s" % (PA, bid))
        out("S5 delete %-20s -> %s %s" % (name, st, raw[:120]))
        time.sleep(1)
    out("== W3 DONE")


if __name__ == "__main__":
    main()
