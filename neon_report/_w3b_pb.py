# -*- coding: utf-8 -*-
"""W3b: schema-only branch on project B (no legacy web-access role "anonymous").
PA gated: 412 "legacy web access role ... role:\"anonymous\"" => PB may pass.
Same isolation probes as W3 (S1 data / S2 so-create / S3 face check / S4 leak
paths P1 child-of-so, P2 PITR@so.parent_lsn, P4 so+parent_lsn) + cleanup.
Self-created data only; X-Bug-Bounty: xxbo on every request.
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
PB = "damp-term-63384673"           # project B (clean target, same account)
TAG = "w3b" + uuid.uuid4().hex[:4]
LOG = r"F:\scan\neon_report\_w3b_out.txt"

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
        st, raw = call("GET", "/projects/%s/branches/%s" % (PB, bid))
        if st == 200:
            b = jget(raw, "branch") or {}
            if b.get("pending_state") == want or (
                    b.get("current_state") == want and b.get("pending_state") is None):
                return True, b
        time.sleep(gap)
    return False, {}


def ensure_endpoint(bid):
    st, raw = call("GET", "/projects/%s/branches/%s/endpoints" % (PB, bid))
    eps = jget(raw, "endpoints") if st == 200 else None
    if isinstance(eps, list) and eps and eps[0].get("host"):
        return eps[0]["host"], "existing"
    st, raw = call("POST", "/projects/%s/endpoints" % PB,
                   {"endpoint": {"branch_id": bid, "type": "read_write"}})
    out("S  endpoint create %s -> %s %s" % (bid, st, raw[:180]))
    for _ in range(40):
        time.sleep(3)
        st, raw = call("GET", "/projects/%s/branches/%s/endpoints" % (PB, bid))
        eps = jget(raw, "endpoints") if st == 200 else None
        if isinstance(eps, list) and eps and eps[0].get("host"):
            return eps[0]["host"], "created"
    return None, "no-endpoint"


def branch_uri(bid, role="neondb_owner"):
    st, raw = call("GET", "/projects/%s/connection_uri?database_name=neondb"
                          "&role_name=%s&branch_id=%s" % (PB, role, bid))
    uri = jget(raw, "uri")
    if not uri:
        return None
    parts = urlsplit(uri)
    q = [(k, v) for k, v in parse_qsl(parts.query) if k != "channel_binding"]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(q), parts.fragment))


def db_q(uri, sql, retries=8):
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
    return ("ERR", str(last)[:220])


def create_branch(name, parent_id, extra=None, with_ep=False):
    branch = {"name": name, "parent_id": parent_id}
    if extra:
        branch.update(extra)
    body = {"branch": branch}
    if with_ep:
        body["endpoints"] = [{"type": "read_write"}]
    st, raw = call("POST", "/projects/%s/branches" % PB, body)
    bid = jget(raw, "branch", "id")
    if st in (200, 201) and bid:
        out("S  create %-18s -> %s id=%s  %s" %
            (name, st, bid, json.dumps(jget(raw, "branch") or {})[:520]))
    else:
        out("S  create %-18s -> %s %s" % (name, st, raw[:300]))
    return st, bid, raw


def main():
    out("== W3b schema-only on PB  tag=%s ==" % TAG)
    created = []
    try:
        return _run(created)
    finally:
        out("S5 cleanup %d" % len(created))
        for name, bid in reversed(created):
            st, raw = call("DELETE", "/projects/%s/branches/%s" % (PB, bid))
            out("S5 delete %-10s -> %s %s" % (name, st, raw[:100]))
            time.sleep(1)
        out("== W3b DONE")


def _run(created):
    # ---- 0. env: branches + roles (web access?) ----
    st, raw = call("GET", "/projects/%s/branches" % PB)
    branches = jget(raw, "branches") or []
    main_id = next((b["id"] for b in branches if b.get("default")), None) \
        or next((b["id"] for b in branches if b.get("name") == "main"), None)
    out("S0 branches=%d main=%s" % (len(branches), main_id))
    st, raw = call("GET", "/projects/%s/branches/%s/roles" % (PB, main_id))
    out("S0 roles on main: %s %s" % (st, raw[:500]))
    roles = jget(raw, "roles") or []
    names = [r.get("name") for r in roles]
    role = next((n for n in ("neondb_owner", "owner", "admin") if n in names), None)
    if not role and names:
        role = names[0]
    out("S0 db role=%s (all=%s)" % (role, names))
    if not main_id:
        out("S0 ABORT no main")
        return

    # ---- S1 src branch + data ----
    st, src_id, raw = create_branch("w3bsrc-%s" % TAG, main_id)
    if not src_id:
        return
    created.append(("w3bsrc", src_id))
    wait_branch(src_id)
    host, how = ensure_endpoint(src_id)
    out("S1 src endpoint=%s (%s)" % (host, how))
    uri = branch_uri(src_id, role)
    if not uri:
        out("S1 ABORT no uri (role=%s)" % role)
        # try every role
        for n in names:
            u2 = branch_uri(src_id, n)
            out("S1 role try %s -> uri=%s" % (n, bool(u2)))
            if u2:
                role, uri = n, u2
                break
    if not uri:
        return
    r = db_q(uri, "SELECT pg_current_wal_lsn()")
    lsn_pre = r[1][0][0] if r[0] == "OK" else None
    db_q(uri, "CREATE TABLE public.so_probe (id serial PRIMARY KEY, secret text)")
    vals = ",".join("('W3PII-%d-%s')" % (i, uuid.uuid4().hex[:12])
                    for i in range(100))
    r = db_q(uri, "INSERT INTO public.so_probe (secret) VALUES %s" % vals)
    out("S1 insert: %s" % (r[0],))
    r = db_q(uri, "SELECT pg_current_wal_lsn()")
    lsn_post = r[1][0][0] if r[0] == "OK" else None
    r = db_q(uri, "SELECT count(*) FROM public.so_probe")
    out("S1 src count: %s %s lsn_pre=%s lsn_post=%s" % (r[0], r[1], lsn_pre, lsn_post))

    # ---- S2 schema-only ----
    st, so_id, raw = create_branch("w3bso-%s" % TAG, src_id,
                                   extra={"init_source": "schema-only"}, with_ep=True)
    if not so_id:
        out("S2 FAILED -> abort")
        for _, bid in created:
            call("DELETE", "/projects/%s/branches/%s" % (PB, bid))
        return
    created.append(("w3bso", so_id))
    ok, b = wait_branch(so_id)
    so_lsn = b.get("parent_lsn")
    out("S2 so ready=%s parent_lsn=%s" % (ok, so_lsn))

    # ---- S3 face check ----
    host2, how2 = ensure_endpoint(so_id)
    out("S3 so endpoint=%s (%s)" % (host2, how2))
    uri2 = branch_uri(so_id, role)
    if not uri2:
        out("S3 ABORT no so uri")
    else:
        r = db_q(uri2, "SELECT to_regclass('public.so_probe')")
        out("S3 so to_regclass: %s %s" % (r[0], r[1]))
        r = db_q(uri2, "SELECT count(*) FROM public.so_probe")
        out("S3 so count: %s %s" % (r[0], r[1]))
        if r[0] == "OK":
            # if relation missing -> schema-only didn't even copy schema; log and continue
            pass

    # ---- S4 leak probes ----
    st, ch_id, raw = create_branch("w3bch-%s" % TAG, so_id, with_ep=True)
    if ch_id:
        created.append(("w3bch", ch_id))
        wait_branch(ch_id)
        host3, _ = ensure_endpoint(ch_id)
        uri3 = branch_uri(ch_id, role)
        r = db_q(uri3, "SELECT count(*) FROM public.so_probe") if uri3 else ("NO-URI", None)
        out("P1 child-of-so count: %s %s" % (r[0], r[1]))

    if so_lsn:
        st, p2_id, raw = create_branch("w3bpitr-%s" % TAG, so_id,
                                       extra={"parent_lsn": so_lsn}, with_ep=True)
        if p2_id:
            created.append(("w3bpitr", p2_id))
            wait_branch(p2_id)
            host4, _ = ensure_endpoint(p2_id)
            uri4 = branch_uri(p2_id, role)
            r = db_q(uri4, "SELECT count(*) FROM public.so_probe") if uri4 else ("NO-URI", None)
            out("P2 pitr@so.parent_lsn count: %s %s" % (r[0], r[1]))
        else:
            out("P2 FAILED: %s %s" % (st, raw[:250]))

    if lsn_post:
        st, p4_id, raw = create_branch("w3bcob-%s" % TAG, src_id,
                                       extra={"init_source": "schema-only",
                                              "parent_lsn": lsn_post}, with_ep=True)
        if p4_id:
            created.append(("w3bcob", p4_id))
            wait_branch(p4_id)
            host5, _ = ensure_endpoint(p4_id)
            uri5 = branch_uri(p4_id, role)
            r = db_q(uri5, "SELECT count(*) FROM public.so_probe") if uri5 else ("NO-URI", None)
            out("P4 so+lsn count: %s %s" % (r[0], r[1]))
        else:
            out("P4 FAILED: %s %s" % (st, raw[:250]))

    # ---- cleanup (finally in main) ----
    out("_run done")


if __name__ == "__main__":
    main()
