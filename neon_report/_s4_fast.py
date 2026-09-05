# -*- coding: utf-8 -*-
"""Neon staging S4 fast-close: AI Gateway / Storage / Credentials cross-proj /
Consumption correct params / Logs fields. All read-only except credential issue
on own branch (revoked at end)."""
import json
import time
import ssl
import http.client
import uuid

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
HB = {"X-Bug-Bounty": "xxbo"}
PA = "orange-sun-90493739"
PAMAIN = "br-wandering-field-w2ob6mpn"
PB = "damp-term-63384673"
PBMAIN = "br-raspy-band-w247957z"
LOG = r"F:\scan\neon_report\_s4_out.jsonl"

with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]

TAG = "s4" + uuid.uuid4().hex[:4]


def log(key, st, out, note=""):
    rec = {"t": time.strftime("%H:%M:%S"), "key": key, "st": st, "note": note,
           "body": (out or "")[:1200]}
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print("[%s] %-46s -> %s %s" % (rec["t"], key, st, note), flush=True)
    if isinstance(st, int) and 400 <= st < 600:
        try:
            e = json.loads(out)
            print("        code=%s msg=%s" % (e.get("code"), e.get("message", "")[:160]),
                  flush=True)
        except Exception:
            print("        raw:", (out or "")[:160], flush=True)


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


def main():
    # --- 1. AI Gateway / Storage presence ---
    for key, path in (
        ("ai_gateway PA main", "/projects/%s/branches/%s/ai_gateway" % (PA, PAMAIN)),
        ("storage PA main", "/projects/%s/branches/%s/storage" % (PA, PAMAIN)),
    ):
        st, out = call("GET", path)
        log(key, st, out)

    # --- 2. Credentials ---
    st, out = call("GET", "/projects/%s/branches/%s/credentials" % (PA, PAMAIN))
    log("creds list PA main", st, out)
    st, out = call("POST", "/projects/%s/branches/%s/credentials" % (PA, PAMAIN),
                   {"name": "s4-%s" % TAG, "scopes": ["storage:read"],
                    "principal_type": "user"})
    log("creds issue PA main", st, out)
    tok = None
    if st in (200, 201):
        tok = json.loads(out).get("token_id")
        log("creds issue got token", 200, out[:200], "token_id=%s" % tok)
    # scope validation probes (own project)
    for sc in (["admin:*"], [], ["storage:read", "storage:write"]):
        st, out = call("POST", "/projects/%s/branches/%s/credentials" % (PA, PAMAIN),
                       {"name": "s4-sc-%s" % TAG, "scopes": sc,
                        "principal_type": "user"})
        log("creds issue scopes=%s" % sc, st, out[:300])
    if tok:
        # normal reveal
        st, out = call("POST", "/projects/%s/branches/%s/credentials/%s/reveal"
                       % (PA, PAMAIN, tok))
        log("creds reveal own", st, out[:400])
        # cross-project path: PB project path with PA token
        st, out = call("POST", "/projects/%s/branches/%s/credentials/%s/reveal"
                       % (PB, PBMAIN, tok))
        log("creds reveal path(PB)+PA token", st, out[:300])
        # cross-project branch: PA path, PB branch
        st, out = call("POST", "/projects/%s/branches/%s/credentials/%s/reveal"
                       % (PA, PBMAIN, tok))
        log("creds reveal path(PA)+PB branch", st, out[:300])
        # rotate cross-project
        st, out = call("POST", "/projects/%s/branches/%s/credentials/%s/rotate"
                       % (PB, PBMAIN, tok), {})
        log("creds rotate path(PB)+PA token", st, out[:300])
        # revoke own (cleanup)
        st, out = call("DELETE", "/projects/%s/branches/%s/credentials/%s"
                       % (PA, PAMAIN, tok))
        log("creds revoke own (cleanup)", st, out[:200])

    # --- 3. Consumption correct params ---
    F = "2026-08-01T00:00:00Z"
    for key, path in (
        ("cons v1 ok", "/consumption_history/projects?project_id=%s&from=%s" % (PA, F)),
        ("cons v2 ok", "/consumption_history/v2/projects?project_id=%s&from=%s" % (PA, F)),
        ("cons v2 br ok", "/consumption_history/v2/branches?project_ids=%s&from=%s"
         % (PA, F)),
        ("cons v1 no proj", "/consumption_history/projects?from=%s" % F),
    ):
        st, out = call("GET", path)
        log(key, st, out[:600])

    # --- 4. Logs fields surface ---
    st, out = call("GET", "/projects/%s/branches/%s/logs/fields" % (PA, PAMAIN))
    log("logs fields PA main", st, out[:600])

    print("== DONE", flush=True)


if __name__ == "__main__":
    main()
