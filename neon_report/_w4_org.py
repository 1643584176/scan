# -*- coding: utf-8 -*-
"""W4: org surface recon (staging).
1) users/me/organizations + org details + members + api_keys + invitations
2) transfer-org spec schema (projects/transfer)
3) keycloak staging-realm registration openness (2nd console account feasibility)
Read-only recon; no mutations. X-Bug-Bounty: xxbo.
"""
import json
import ssl
import http.client

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
HB = {"X-Bug-Bounty": "xxbo"}
with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]


def api(method, path):
    try:
        ctx = ssl.create_default_context()
        conn = http.client.HTTPSConnection(API_HOST, timeout=30, context=ctx)
        conn.request(method, API_BASE + path,
                     headers=dict(HB, Authorization="Bearer " + APIKEY))
        resp = conn.getresponse()
        data = resp.read().decode("utf-8", "replace")
        conn.close()
        return resp.status, data
    except Exception as e:
        return None, str(e)[:150]


def show(tag, st, raw, cut=700):
    print("\n== %s -> %s" % (tag, st))
    print(raw[:cut])
    return raw


st, raw = api("GET", "/users/me/organizations")
raw = show("orgs of me", st, raw)
orgs = []
try:
    orgs = json.loads(raw).get("organizations", [])
except Exception:
    pass

for o in orgs[:5]:
    oid = o.get("id")
    show("org detail %s" % oid, *api("GET", "/organizations/%s" % oid), 400)
    show("org members %s" % oid, *api("GET", "/organizations/%s/members" % oid), 900)
    show("org api_keys %s" % oid, *api("GET", "/organizations/%s/api_keys" % oid), 500)
    show("org invitations %s" % oid, *api("GET", "/organizations/%s/invitations" % oid), 500)
    show("org spending_limit %s" % oid,
         *api("GET", "/organizations/%s/billing/spending_limit" % oid), 400)

# transfer schema from spec
spec = json.load(open(r"F:\scan\neon_report\_openapi_v2.json", encoding="utf-8"))
p = spec["paths"]["/organizations/{source_org_id}/projects/transfer"]["post"]
ref = p.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
print("\n== transfer requestBody:", json.dumps(ref)[:300])
name = ref.get("$ref", "").rsplit("/", 1)[-1]
if name:
    s = spec["components"]["schemas"].get(name, {})
    print("SCHEMA", name, "required:", s.get("required"))
    print("props:", json.dumps(s.get("properties", {}))[:900])
print("resp200:", json.dumps(p.get("responses", {}).get("200", {}))[:200])

# keycloak realm: registration open?
try:
    ctx = ssl.create_default_context()
    conn = http.client.HTTPSConnection(API_HOST, timeout=30, context=ctx)
    conn.request("GET", "/realms/staging-realm/.well-known/openid-configuration")
    resp = conn.getresponse()
    d = resp.read().decode("utf-8", "replace")
    conn.close()
    cfg = json.loads(d)
    reg = cfg.get("registration_endpoint")
    print("\n== KC registration_endpoint:", reg)
except Exception as e:
    print("\n== KC ERR", e)
try:
    ctx = ssl.create_default_context()
    conn = http.client.HTTPSConnection(API_HOST, timeout=30, context=ctx)
    conn.request("GET", "/realms/staging-realm")
    resp = conn.getresponse()
    d = resp.read().decode("utf-8", "replace")
    conn.close()
    r = json.loads(d)
    print("realm registrationAllowed:", r.get("registrationAllowed"),
          "| verifyEmail:", r.get("verifyEmail"),
          "| registrationEmailAsUsername:", r.get("registrationEmailAsUsername"))
except Exception as e:
    print("realm cfg ERR", e)
print("\n== W4 recon DONE")
