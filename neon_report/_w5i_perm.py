# -*- coding: utf-8 -*-
"""W5i: permissions invite semantics + transfer_requests/recover probing (self-scoped)."""
import json, ssl, http.client, time

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
PA = "orange-sun-90493739"
with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]
ctx = ssl.create_default_context()

def api(method, path, body=None):
    conn = http.client.HTTPSConnection(API_HOST, timeout=30, context=ctx)
    hdr = {"X-Bug-Bounty": "xxbo", "Authorization": "Bearer " + APIKEY}
    if body is not None:
        hdr["Content-Type"] = "application/json"
        body = json.dumps(body)
    conn.request(method, API_BASE + path, body=body, headers=hdr)
    r = conn.getresponse()
    data = r.read().decode("utf-8", "replace")
    conn.close()
    return r.status, data

# X1: grant permission to never-registered email
st, d = api("POST", "/projects/%s/permissions" % PA, {"email": "definitely-not-registered-9f3k2x@gmail.com"})
print("X1 grant to unregistered: %d %s" % (st, d[:300]))

# X2: grant permission to own email (self)
st, d = api("POST", "/projects/%s/permissions" % PA, {"email": "libobo1229@gmail.com"})
print("X2 grant to self: %d %s" % (st, d[:300]))

# X2b: check list now
st, d = api("GET", "/projects/%s/permissions" % PA)
print("X2b list: %d %s" % (st, d[:500]))

# X3: members list
st, d = api("GET", "/projects/%s/members" % PA)
print("X3 members: %d %s" % (st, d[:400]))

# X4: transfer_requests empty body + plausible bodies
for tag, body in [("empty", None), ("org target", {"organization_id": "org-flat-dawn-91601224"}),
                  ("email target", {"email": "libobo1229@gmail.com"})]:
    st, d = api("POST", "/projects/%s/transfer_requests" % PA, body)
    print("X4 transfer %s: %d %s" % (tag, st, d[:300]))
    time.sleep(0.5)

# X5: recover on live project
st, d = api("POST", "/projects/%s/recover" % PA, {})
print("X5 recover live: %d %s" % (st, d[:300]))
