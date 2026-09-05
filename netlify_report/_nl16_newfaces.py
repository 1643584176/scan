# -*- coding: utf-8 -*-
"""NL16: untested endpoint families - ai-gateway/token, assets, forms/submissions (read-only + cross-account)"""
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


def show(label, st, b, trunc=600):
    print("%-46s [%d] %s" % (label, st, b[:trunc].replace("\n", " ")), flush=True)


def main():
    print("== NL16 ==", flush=True)
    # find team uuid from user object
    st, b = api("GET", "/api/v1/user", TOKEN_A)
    show("user(A)", st, b, 800)
    try:
        u = json.loads(b)
        team_id = (u.get("account_slug") or "")
        accs = u.get("accounts") or []
        print("accounts:", [(a.get("slug"), a.get("id")) for a in accs], flush=True)
    except Exception as e:
        print("user parse fail", e, flush=True)

    # ai-gateway token - site level (A self / B cross / anon)
    show("ai-gw/sites/A self", *api("GET", "/api/v1/sites/%s/ai-gateway/token" % SITE_A, TOKEN_A))
    show("ai-gw/sites/A via B", *api("GET", "/api/v1/sites/%s/ai-gateway/token" % SITE_A, TOKEN_B))
    show("ai-gw/sites/B self", *api("GET", "/api/v1/sites/%s/ai-gateway/token" % SITE_B_ID, TOKEN_B))
    show("ai-gw/anon", *api("GET", "/api/v1/sites/%s/ai-gateway/token" % SITE_A))
    # account level - guess both slug & id forms
    for acc in ("1643584176", "libobo01"):
        show("ai-gw/acc %s A" % acc, *api("GET", "/api/v1/accounts/%s/ai-gateway/token" % acc, TOKEN_A))
    # assets
    show("assets A self", *api("GET", "/api/v1/sites/%s/assets" % SITE_A, TOKEN_A))
    show("assets A via B", *api("GET", "/api/v1/sites/%s/assets" % SITE_A, TOKEN_B))
    # forms + submissions
    show("forms A self", *api("GET", "/api/v1/sites/%s/forms" % SITE_A, TOKEN_A))
    show("forms B self", *api("GET", "/api/v1/sites/%s/forms" % SITE_B_ID, TOKEN_B))
    show("forms A via B", *api("GET", "/api/v1/sites/%s/forms" % SITE_A, TOKEN_B))
    print("done", flush=True)


if __name__ == "__main__":
    main()
