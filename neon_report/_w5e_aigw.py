# -*- coding: utf-8 -*-
"""W5e: AI gateway recon - protocol, auth model, scope checks."""
import json, ssl, http.client, time

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
PA = "orange-sun-90493739"
PAMAIN = "br-wandering-field-w2ob6mpn"
with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]
ctx = ssl.create_default_context()

def api(method, path, body=None, key=APIKEY, host=API_HOST, base=API_BASE):
    conn = http.client.HTTPSConnection(host, timeout=30, context=ctx)
    hdr = {"X-Bug-Bounty": "xxbo", "Authorization": "Bearer " + key}
    if body is not None:
        hdr["Content-Type"] = "application/json"
        body = json.dumps(body)
    conn.request(method, base + path, body=body, headers=hdr)
    r = conn.getresponse()
    data = r.read().decode("utf-8", "replace")
    conn.close()
    return r.status, data

# 1. full credentials list
st, data = api("GET", "/projects/%s/branches/%s/credentials" % (PA, PAMAIN))
print("== credentials:", st, data)
creds = json.loads(data) if st == 200 else []
for c in creds.get("credentials", []):
    print("  token:", c)

# 2. ai_gateway details
st, data = api("GET", "/projects/%s/branches/%s/ai_gateway" % (PA, PAMAIN))
print("== ai_gateway:", st, data)
gw = json.loads(data) if st == 200 else {}
base = gw.get("base_url", "")

# 3. probe gateway protocol (no auth first)
def raw(host, path, headers=None, method="GET", body=None):
    conn = http.client.HTTPSConnection(host, timeout=20, context=ctx)
    conn.request(method, path, body=body, headers=headers or {})
    r = conn.getresponse()
    d = r.read().decode("utf-8", "replace")
    conn.close()
    return r.status, dict(r.getheaders()), d

if base:
    h = base.split("//")[1].split("/")[0]
    for p in ("/", "/v1/models", "/health", "/v1/chat/completions"):
        try:
            st2, hd, d = raw(h, p)
            keep = {k: v for k, v in hd.items()
                    if k.lower() in ("server", "content-type", "www-authenticate", "x-request-id", "x-neon-project-id")}
            print("== gw %s -> %d | %s | %s" % (p, st2, keep, d[:220]))
        except Exception as e:
            print("== gw %s ERR %s" % (p, e))
        time.sleep(0.3)
