# -*- coding: utf-8 -*-
"""U18: triage follow-up - verify the 'viewer-scoped API key' premise.
Q from triage: how is a viewer-scoped API key generated via UI?
Plan: (0) fetch live staging spec ApiKeyCreateRequest, (1) POST /api_keys matrix
with malformed scope payloads, (2) response echo + list readback, (3) org-key
project_id scope (only documented mechanism) enforcement probe, (4) cleanup.
Zero-destruction: own project, temp keys deleted at the end."""
import json
import ssl
import time
import http.client
import urllib.request

HOST = "console-stage.neon.build"
BASE = "/api/v2"
HB = {"X-Bug-Bounty": "xxbo"}
PA = "orange-sun-90493739"
PB = "damp-term-63384673"
ORG = "org-flat-dawn-91601224"
LOG = r"F:\scan\neon_report\_u18_out.txt"

with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    MAINKEY = json.load(fh)["key"]


def out(s):
    print(s, flush=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(s + "\n")


def call(method, path, body=None, key=MAINKEY, timeout=45):
    ctx = ssl.create_default_context()
    conn = http.client.HTTPSConnection(HOST, timeout=timeout, context=ctx)
    payload = json.dumps(body) if body is not None else None
    hdrs = dict(HB, Authorization="Bearer " + key)
    if body is not None:
        hdrs["Content-Type"] = "application/json"
    conn.request(method, BASE + path, body=payload, headers=hdrs)
    r = conn.getresponse()
    data = r.read().decode("utf-8", "replace")
    conn.close()
    return r.status, data


def list_personal_keys():
    st, d = call("GET", "/api_keys")
    try:
        j = json.loads(d)
        return st, j if isinstance(j, list) else j.get("api_keys", [])
    except Exception:
        return st, []


# ---- 0. live spec ----
out("== 0. live spec ==")
for url in ["https://%s/api/v2/openapi.json" % HOST, "https://%s/openapi.json" % HOST]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "X-Bug-Bounty": "xxbo"})
        data = urllib.request.urlopen(req, context=ssl.create_default_context(), timeout=60).read()
        spec = json.loads(data.decode("utf-8", "replace"))
        out("spec OK %s len=%d" % (url, len(data)))
        schemas = spec.get("components", {}).get("schemas", {})
        for n in ("ApiKeyCreateRequest", "OrgApiKeyCreateRequest", "OrgApiKeyCreateResponse"):
            s = schemas.get(n)
            if s is None:
                out("  %s: ABSENT" % n)
            else:
                out("  %s: %s" % (n, json.dumps(s)[:700]))
        break
    except Exception as e:
        out("spec %s ERR %s" % (url, str(e)[:200]))

# ---- cleanup previous u18 keys ----
st, keys = list_personal_keys()
for k in keys:
    if str(k.get("name", "")).startswith("u18"):
        call("DELETE", "/api_keys/%s" % k.get("id"))

# ---- 1. creation matrix ----
out("\n== 1. POST /api_keys matrix ==")
matrix = [
    ("A valid viewer scope", {"key_name": "u18-a", "scope": {"project_id": PA, "permission": "viewer"}}),
    ("B bogus permission", {"key_name": "u18-b", "scope": {"project_id": PA, "permission": "totally-bogus"}}),
    ("C scope wrong type", {"key_name": "u18-c", "scope": "not-an-object"}),
    ("D unknown junk field", {"key_name": "u18-d", "totally_unknown_xyz": {"a": 1}}),
    ("E flat project_id", {"key_name": "u18-e", "project_id": PA}),
]
keys_by_tag = {}
for tag, body in matrix:
    st, d = call("POST", "/api_keys", body)
    echo = '"scope"' in d
    out("[%s] %d echo_scope=%s resp=%s" % (tag, st, echo, d[:260]))
    if st in (200, 201):
        try:
            keys_by_tag[tag[0]] = json.loads(d)
        except Exception:
            pass
    time.sleep(0.4)

# ---- 2. readback via list ----
out("\n== 2. readback GET /api_keys ==")
st, keys = list_personal_keys()
for k in keys:
    if str(k.get("name", "")).startswith("u18"):
        out("  item: %s" % json.dumps(k)[:260])

# ---- 3. probes ----
out("\n== 3. probes ==")
# B key (garbage permission) - is it a working full credential?
bk = keys_by_tag.get("B", {}).get("key")
if bk:
    st, d = call("GET", "/projects/%s/branches" % PA, key=bk)
    out("B(garbage scope) GET branches PA: %d %s" % (st, d[:120]))
    st, d = call("GET", "/projects/%s/tmp-not-used" % PA, key=bk)
    out("B(garbage scope) GET junk path: %d" % st)

# E key (flat project_id) - cross-project reach?
ek = keys_by_tag.get("E", {}).get("key")
if ek:
    st, d = call("GET", "/projects/%s/branches" % PB, key=ek)
    out("E(flat project_id=PA) GET branches PB(OTHER): %d %s" % (st, d[:120]))

# org key with project_id (documented mechanism)
out("-- org key project_id probe --")
st, d = call("POST", "/organizations/%s/api_keys" % ORG, {"key_name": "u18-g", "project_id": PA})
out("create org key: %d resp=%s" % (st, d[:300]))
gk, gid = None, None
try:
    j = json.loads(d)
    gk, gid = j.get("key"), j.get("id")
except Exception:
    pass
if gk:
    st, d = call("GET", "/projects/%s" % PA, key=gk)
    out("G GET project PA (own scope): %d %s" % (st, d[:120]))
    st, d = call("GET", "/projects/%s/branches" % PB, key=gk)
    out("G GET branches PB (other project): %d %s" % (st, d[:160]))
    st, d = call("GET", "/projects", key=gk)
    out("G GET /projects list: %d %s" % (st, d[:200]))

# ---- 4. cleanup ----
out("\n== 4. cleanup ==")
st, keys = list_personal_keys()
for k in keys:
    if str(k.get("name", "")).startswith("u18"):
        st2, d2 = call("DELETE", "/api_keys/%s" % k.get("id"))
        out("del %s: %d" % (k.get("name"), st2))
if gid:
    st, d = call("DELETE", "/organizations/%s/api_keys/%s" % (ORG, gid))
    out("del org key u18-g: %d %s" % (st, d[:160]))
st, keys = list_personal_keys()
out("remaining: %s" % [k.get("name") for k in keys])
out("== DONE")
