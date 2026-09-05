# -*- coding: utf-8 -*-
"""Probe hidden write endpoints with minimal bodies (zero-destruction).
Core: runProjectQuery execution identity (current_user / rolsuper probe).
"""
import json
import time
import ssl
import http.client

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
HB = {"X-Bug-Bounty": "xxbo"}
PA = "orange-sun-90493739"
PAMAIN = "br-wandering-field-w2ob6mpn"
EP = "ep-crimson-fog-w2gucld1"
LOG = r"F:\scan\neon_report\_u2_out.jsonl"

with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]


def log(key, st, out, note=""):
    rec = {"t": time.strftime("%H:%M:%S"), "key": key, "st": st, "note": note,
           "body": (out or "")[:800]}
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print("[%s] %-48s -> %s %s" % (rec["t"], key, st, note), flush=True)
    if isinstance(st, int) and 400 <= st < 600:
        try:
            e = json.loads(out)
            print("        code=%s msg=%s" % (e.get("code"), e.get("message", "")[:200]),
                  flush=True)
        except Exception:
            print("        raw:", (out or "")[:200], flush=True)


def call(method, path, body=None, timeout=30):
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


# 1. SQL query execution identity probes (read-only SQL only)
for label, q in (
    ("query current_user", "select current_user"),
    ("query rolsuper", "select rolsuper from pg_roles where rolname=current_user"),
    ("query session_user", "select session_user"),
    ("query neon ctx", "select current_setting('neon.tenant_id', true)"),
):
    for body in ({"query": q}, {"sql": q}, {"statement": q}, {"query_text": q}):
        st, out = call("POST", "/projects/%s/query" % PA, body)
        if st != 400 or "query" not in out.lower():
            log("%s body=%s" % (label, list(body)[0]), st, out)
            break
        log("schema try %s" % list(body)[0], st, out[:200])
    time.sleep(0.4)

# 2. AI gateway global endpoints
st, out = call("GET", "/ai_gateway/models")
log("ai_gateway/models", st, out)
st, out = call("POST", "/ai_gateway/resolve_identity", {})
log("ai_gateway/resolve_identity", st, out)

# 3. passwordless auth
st, out = call("POST", "/projects/%s/endpoints/%s/passwordless_auth" % (PA, EP), {})
log("passwordless_auth {}", st, out)

# 4. auth/init OAuth
for ap in ("better_auth", "neon_auth", "mock", "stack"):
    st, out = call("GET", "/projects/%s/auth/init?auth_provider=%s" % (PA, ap))
    log("auth/init provider=%s" % ap, st, out)
    time.sleep(0.3)

# 5. reset on a FRESH temp branch (zero destruction)
st, out = call("POST", "/projects/%s/branches" % PA,
               {"branch": {"name": "u2-tmp", "parent_id": PAMAIN}})
log("create u2-tmp branch", st, out)
bid = json.loads(out).get("branch", {}).get("id") if st in (200, 201) else None
if bid:
    time.sleep(4)
    st, out = call("POST", "/projects/%s/branches/%s/reset" % (PA, bid), {})
    log("reset temp {} body", st, out)
    st, out = call("POST", "/projects/%s/branches/%s/reset_to_parent" % (PA, bid), {})
    log("reset_to_parent temp", st, out)
    st, out = call("POST", "/projects/%s/branches/%s/recover" % (PA, bid), {})
    log("recover temp (not deleted)", st, out)
    # cleanup
    st, out = call("DELETE", "/projects/%s/branches/%s" % (PA, bid))
    log("cleanup u2-tmp", st, out)

# 6. saved query + history writes (minimal)
st, out = call("POST", "/projects/%s/saved_queries" % PA,
               {"name": "u2-q", "query": "select 1", "branch_id": PAMAIN})
log("saved_queries create", st, out)
st, out = call("POST", "/projects/%s/query/history" % PA,
               {"query": "select 1", "branch_id": PAMAIN})
log("query/history add", st, out)
print("== DONE", flush=True)
