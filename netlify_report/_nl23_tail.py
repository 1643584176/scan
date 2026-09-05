# -*- coding: utf-8 -*-
"""NL23: tail-end untested families - oauth/tickets, purge, deploy_keys (read-only + structure probes)"""
import http.client, ssl, json, sys
sys.path.insert(0, r'F:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B, SITE_A

ctx = ssl.create_default_context()
SITE_B_ID = 'd2977de0-d24d-4544-81cb-933e610cad7d'


def api(method, path, token=None, body=None):
    conn = http.client.HTTPSConnection("api.netlify.com", timeout=30, context=ctx)
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


def show(label, st, b, trunc=400):
    print("%-44s [%d] %s" % (label, st, b[:trunc].replace("\n", " ")), flush=True)


def main():
    print("== NL23 ==", flush=True)
    # 1. oauth tickets structure (no valid client_id - expect 4xx hint)
    show("oauth tickets POST {}", *api("POST", "/api/v1/oauth/tickets", TOKEN_A, {}))
    show("oauth tickets POST noauth", *api("POST", "/api/v1/oauth/tickets"))
    show("oauth tickets GET self", *api("GET", "/api/v1/oauth/tickets", TOKEN_A))
    show("oauth ticket exchange noauth", *api("POST", "/api/v1/oauth/tickets/00000000-0000-0000-0000-000000000000/exchange"))
    show("oauth ticket GET noauth", *api("GET", "/api/v1/oauth/tickets/00000000-0000-0000-0000-000000000000"))
    # 2. purge (no site context - global endpoint)
    show("purge POST anon", *api("POST", "/api/v1/purge", None, {}))
    show("purge POST A", *api("POST", "/api/v1/purge", TOKEN_A, {}))
    show("purge POST A site", *api("POST", "/api/v1/purge", TOKEN_A, {"site_id": SITE_A}))
    show("purge POST B site via A", *api("POST", "/api/v1/purge", TOKEN_A, {"site_id": SITE_B_ID}))
    # 3. deploy_keys real resources
    show("deploy_keys GET A", *api("GET", "/api/v1/deploy_keys", TOKEN_A))
    show("deploy_keys POST A", *api("POST", "/api/v1/deploy_keys", TOKEN_A))
    show("deploy_keys GET B", *api("GET", "/api/v1/deploy_keys", TOKEN_B))
    print("done", flush=True)


if __name__ == "__main__":
    main()
