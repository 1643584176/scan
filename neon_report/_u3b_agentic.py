# -*- coding: utf-8 -*-
"""Probe: can we CREATE an agentic account request via api/v2? What body?
Also scan _api_doc.md / openapi for agentic paths."""
import json
import time
import ssl
import uuid
import re
import http.client

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
HB = {"X-Bug-Bounty": "xxbo"}
LOG = r"F:\scan\neon_report\_u3b_out.jsonl"

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


# 1. does api doc mention agentic?
for f in (r"F:\scan\neon_report\_api_doc.md",):
    try:
        t = open(f, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r"agentic[^\n]{0,150}", t, re.I):
            print("doc hit:", m.group(0)[:160], flush=True)
    except Exception as e:
        print("doc err", e, flush=True)

# 2. try CREATE variants (empty bodies - only decode errors expected)
for path, body in (
    ("/agentic_provisioning/account_requests", {}),
    ("/agentic_provisioning/account_requests", {"orchestrator": "stripe", "email": "a@b.c"}),
    ("/agentic_provisioning/account_requests/stripe", {"email": "a@b.c"}),
):
    st, out = call("POST", path, body)
    log("POST create %s" % path, st, out)
    time.sleep(0.3)

# 3. try list endpoints
for path in ("/agentic_provisioning/account_requests",
             "/agentic_provisioning/requests",
             "/agentic_provisioning/account_requests/mine",
             "/agentic_provisioning/connections",
             "/agentic_provisioning"):
    st, out = call("GET", path)
    log("GET list %s" % path, st, out)
    time.sleep(0.2)
print("== DONE", flush=True)
