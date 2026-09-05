# -*- coding: utf-8 -*-
"""NL17: ai-gateway deep recon - account token, /.netlify/ai/ endpoint structure, providers detail"""
import http.client, ssl, json, sys
sys.path.insert(0, r'F:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B, SITE_A

ctx = ssl.create_default_context()
SITE_B_ID = 'd2977de0-d24d-4544-81cb-933e610cad7d'
TEAM_A_UUID = '6a979dd2ae93f47d55b62897'


def api(method, path, token=None, body=None, host="api.netlify.com"):
    conn = http.client.HTTPSConnection(host, timeout=30, context=ctx)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept': 'application/json'}
    if token:
        h['Authorization'] = 'Bearer ' + token
    if body is not None:
        h['Content-Type'] = 'application/json'
    conn.request(method, path, json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse()
    raw = r.read().decode("utf-8", "replace")
    conn.close()
    return r.status, raw


def show(label, st, b, trunc=700):
    print("%-46s [%d] %s" % (label, st, b[:trunc].replace("\n", " ")), flush=True)


def main():
    print("== NL17 ==", flush=True)
    # B team uuid
    st, b = api("GET", "/api/v1/user", TOKEN_B)
    show("user(B)", st, b, 700)
    try:
        u = json.loads(b)
        print("B account_id:", u.get("account_id"), "slug:", u.get("slug"), flush=True)
    except Exception:
        pass
    # account-level ai-gateway token with proper uuid
    show("ai-gw/acc A uuid", *api("GET", "/api/v1/accounts/%s/ai-gateway/token" % TEAM_A_UUID, TOKEN_A))
    show("ai-gw/acc A uuid via B", *api("GET", "/api/v1/accounts/%s/ai-gateway/token" % TEAM_A_UUID, TOKEN_B))
    # providers detail (what config fields exist - base_url?)
    show("ai-gw/providers anon", *api("GET", "/api/v1/ai-gateway/providers"))
    # /.netlify/ai/ endpoint structure on B site (alive site)
    hdr = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept': 'application/json',
           'Cookie': None}
    st, b = api("GET", "/.netlify/ai/", None, host="sec-b-08v4pk.netlify.app")
    show("B /.netlify/ai/ GET anon", st, b, 400)
    st, b = api("OPTIONS", "/.netlify/ai/", None, host="sec-b-08v4pk.netlify.app")
    print("B /.netlify/ai/ OPTIONS [%d] %s" % (st, b[:400].replace("\n", " ")), flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
