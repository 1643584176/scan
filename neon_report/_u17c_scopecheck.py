# -*- coding: utf-8 -*-
"""U17C: sanity check - does the viewer scope actually restrict writes?
If viewer key can DELETE/PATCH/anonymize, the scope is not enforced on staging
and the u17b chain conclusion is void. Control probes under the viewer key.
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
LOG = r"F:\scan\neon_report\_u17c_out.txt"

with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    MAINKEY = json.load(fh)["key"]


def out(s):
    print(s, flush=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(s + "\n")


def call(method, path, body=None, key=MAINKEY, timeout=60):
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


# ---- cleanup + create viewer key ----
st, d = call("GET", "/api_keys")
for k in json.loads(d) if isinstance(json.loads(d), list) else json.loads(d).get("api_keys", []):
    if k.get("name", "").startswith("u17"):
        call("DELETE", "/api_keys/%s" % k["id"])
st, d = call("POST", "/api_keys", {"key_name": "u17c-viewer",
                                   "scope": {"project_id": PA, "permission": "viewer"}})
VKEY = json.loads(d).get("key")
out("viewer key: %s" % (VKEY[:16] + "..." if VKEY else "FAIL"))
st, d = call("GET", "/api_keys", key=VKEY)
out("viewer can list api_keys: %s %s" % (st, d[:200]))

# create temp branch with MAIN key for mutation probes
st, d = call("POST", "/projects/%s/branches" % PA,
             {"branch": {"name": "u17c-tmp", "parent_id": PAMAIN}})
TMP = json.loads(d)["branch"]["id"]
out("tmp branch: %s" % TMP)

out("\n=== write probes under viewer key ===")
st, d = call("PATCH", "/projects/%s/branches/%s" % (PA, TMP),
             {"branch": {"name": "u17c-hijack"}}, key=VKEY)
out("viewer PATCH rename branch: %s %s" % (st, d[:200]))
st, d = call("POST", "/projects/%s/branches" % PA,
             {"branch": {"name": "u17c-fork2", "parent_id": PAMAIN}}, key=VKEY)
out("viewer fork2: %s" % st)
if st in (200, 201):
    f2 = json.loads(d)["branch"]["id"]
    st2, d2 = call("DELETE", "/projects/%s/branches/%s" % (PA, f2), key=VKEY)
    out("viewer DELETE fork2: %s %s" % (st2, d2[:200]))
st, d = call("POST", "/projects/%s/branch_anonymized" % PA, {
    "branch_create": {"branch": {"name": "u17c-anon", "parent_id": PAMAIN}},
    "masking_rules": [{"database_name": "neondb", "schema_name": "public",
                       "table_name": "x", "column_name": "y",
                       "masking_function": "anon.fake_email()"}],
    "start_anonymization": False,
}, key=VKEY)
out("viewer branch_anonymized: %s %s" % (st, d[:250]))
st, d = call("POST", "/projects/%s/branches/%s/roles/neondb_owner/reset_password" % (PA, PAMAIN), {}, key=VKEY)
out("viewer reset_password(main): %s %s" % (st, d[:150]))
st, d = call("POST", "/projects/%s/branches/%s/set_as_default" % (PA, TMP), {}, key=VKEY)
out("viewer set_as_default(tmp): %s %s" % (st, d[:150]))

# restore tmp name + cleanup via main key
call("PATCH", "/projects/%s/branches/%s" % (PA, TMP), {"branch": {"name": "u17c-tmp"}})
st, d = call("DELETE", "/projects/%s/branches/%s" % (PA, TMP))
out("cleanup tmp: %s" % st)
st, d = call("GET", "/api_keys")
for k in json.loads(d) if isinstance(json.loads(d), list) else json.loads(d).get("api_keys", []):
    if k.get("name", "").startswith("u17"):
        call("DELETE", "/api_keys/%s" % k["id"])
out("keys cleaned")
out("== DONE")
