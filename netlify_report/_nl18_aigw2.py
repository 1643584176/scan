# -*- coding: utf-8 -*-
"""NL18: ai-gateway request schema probe on B site (no real inference - invalid values only)"""
import http.client, ssl, json, sys
sys.path.insert(0, r'F:\scan\netlify_report')
from _net_creds import TOKEN_B, COOKIE_B

ctx = ssl.create_default_context()
SITE_B_ID = 'd2977de0-d24d-4544-81cb-933e610cad7d'
B_DOMAIN = 'sec-b-08v4pk.netlify.app'


def api(method, path, token=None, body=None, host="api.netlify.com", extra=None):
    conn = http.client.HTTPSConnection(host, timeout=40, context=ctx)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept': 'application/json'}
    if token:
        h['Authorization'] = 'Bearer ' + token
    if body is not None:
        h['Content-Type'] = 'application/json'
    if extra:
        h.update(extra)
    conn.request(method, path, json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse()
    raw = r.read().decode("utf-8", "replace")
    conn.close()
    return r.status, raw


def main():
    print("== NL18 ==", flush=True)
    # 1. site token for B
    st, b = api("GET", "/api/v1/sites/%s/ai-gateway/token" % SITE_B_ID, TOKEN_B)
    print("B token [%d] %s" % (st, b[:200]), flush=True)
    tok = None
    url = None
    try:
        j = json.loads(b)
        tok = j.get("token")
        url = j.get("url")
    except Exception as e:
        print("parse fail", e, flush=True)
    if not tok:
        print("no token", flush=True)
        return
    # 2. probe /.netlify/ai/ schema with the token (invalid bodies, expect 4xx schema hints before provider call)
    probes = [
        ("empty body", None),
        ("{}", {}),
        ("{model}", {"model": "x"}),
        ("openai-style", {"model": "claude-sonnet-4-5", "messages": [{"role": "user", "content": "hi"}]}),
        ("provider+model", {"provider": "anthropic", "model": "definitely-not-a-model-xyz", "messages": []}),
        ("no auth probe", None),
    ]
    for label, body in probes:
        st, b = api("POST", "/.netlify/ai/", tok if label != "no auth probe" else None,
                    body, host=B_DOMAIN)
        print("%-22s [%d] %s" % (label, st, b[:400].replace("\n", " ")), flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
