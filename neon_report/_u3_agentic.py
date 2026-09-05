# -*- coding: utf-8 -*-
"""Probe agentic_provisioning endpoints (zero-destruction: random uuids only).
Auth model: page uses cookie+X-CSRF; test whether Bearer API key is accepted,
and map 401/403/404 ordering for orchestrator+id enumeration.
"""
import json
import time
import ssl
import uuid
import http.client

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
HB = {"X-Bug-Bounty": "xxbo"}
LOG = r"F:\scan\neon_report\_u3_out.jsonl"

with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]


def log(key, st, out, note=""):
    rec = {"t": time.strftime("%H:%M:%S"), "key": key, "st": st, "note": note,
           "body": (out or "")[:900]}
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print("[%s] %-52s -> %s %s" % (rec["t"], key, st, note), flush=True)
    if isinstance(st, int) and 400 <= st < 600:
        try:
            e = json.loads(out)
            print("        code=%s msg=%s" % (e.get("code"), e.get("message", "")[:250]),
                  flush=True)
        except Exception:
            print("        raw:", (out or "")[:250], flush=True)


def call(method, path, body=None, timeout=30, hdrs_extra=None):
    ctx = ssl.create_default_context()
    conn = http.client.HTTPSConnection(API_HOST, timeout=timeout, context=ctx)
    payload = json.dumps(body) if body is not None else None
    hdrs = dict(HB, Authorization="Bearer " + APIKEY)
    if body is not None:
        hdrs["Content-Type"] = "application/json"
    if hdrs_extra:
        hdrs.update(hdrs_extra)
    conn.request(method, API_BASE + path, body=payload, headers=hdrs)
    resp = conn.getresponse()
    data = resp.read().decode("utf-8", "replace")
    conn.close()
    return resp.status, data


U1 = str(uuid.uuid4())
U2 = str(uuid.uuid4())

# 1. no-auth GET (no Authorization header at all)
ctx = ssl.create_default_context()
conn = http.client.HTTPSConnection(API_HOST, timeout=30, context=ctx)
conn.request("GET", API_BASE + "/agentic_provisioning/account_requests/stripe/%s" % U1,
             headers=dict(HB))
resp = conn.getresponse()
d = resp.read().decode("utf-8", "replace")
conn.close()
log("noauth GET stripe/uuid", resp.status, d)

# 2. API-key GET: random uuid per orchestrator
for orch in ("stripe", "neon", "databricks", "vercel", "github", "anthropic"):
    st, out = call("GET", "/agentic_provisioning/account_requests/%s/%s" % (orch, U1))
    log("GET orch=%s" % orch, st, out)
    time.sleep(0.25)

# 3. API-key GET with different uuid (check 404 vs 403 distinction)
st, out = call("GET", "/agentic_provisioning/account_requests/stripe/%s" % U2)
log("GET stripe/uuid2", st, out)

# 4. POST approve on nonexistent id
st, out = call("POST", "/agentic_provisioning/account_requests/stripe/%s/approve" % U1, {})
log("approve stripe/uuid", st, out)

# 5. path traversal / weird orchestrator
for p in ("stripe/../../projects", "stripe/%2e%2e", "stripe/0", "stripe/x" * 20):
    st, out = call("GET", "/agentic_provisioning/account_requests/%s" % p)
    log("weird path %s" % p[:40], st, out)
    time.sleep(0.2)
print("== DONE", flush=True)
