# -*- coding: utf-8 -*-
"""NL19: ai-gateway schema probe - single process (same egress IP for token fetch + request)"""
import http.client, ssl, json, sys
sys.path.insert(0, r'F:\scan\netlify_report')
from _net_creds import TOKEN_B

ctx = ssl.create_default_context()
SITE_B_ID = 'd2977de0-d24d-4544-81cb-933e610cad7d'
B_DOMAIN = 'sec-b-08v4pk.netlify.app'


def api(method, path, token=None, body=None, host="api.netlify.com"):
    conn = http.client.HTTPSConnection(host, timeout=40, context=ctx)
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


def main():
    print("== NL19 ==", flush=True)
    st, b = api("GET", "/api/v1/sites/%s/ai-gateway/token" % SITE_B_ID, TOKEN_B)
    print("token [%d]" % st, flush=True)
    try:
        j = json.loads(b)
        tok = j.get("token")
        import base64
        payload = tok.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        claims = json.loads(base64.urlsafe_b64decode(payload))
        print("claims source_ip:", claims.get("source_ip"), "site:", claims.get("site_id"), flush=True)
    except Exception as e:
        print("token parse fail", e, flush=True)
        return
    # probe schema with valid-ish bodies (invalid model -> provider 4xx, no real cost)
    probes = [
        ("provider+model+msgs", {"provider": "anthropic", "model": "zz-no-such-model", "messages": [{"role": "user", "content": "hi"}]}),
        ("openai-style", {"model": "zz-no-such-model", "messages": [{"role": "user", "content": "hi"}]}),
        ("provider only", {"provider": "anthropic"}),
        ("chat path?", None),
    ]
    for label, body in probes:
        st, b = api("POST", "/.netlify/ai/", tok, body, host=B_DOMAIN)
        print("%-22s [%d] %s" % (label, st, b[:500].replace("\n", " ")), flush=True)
    # maybe subpaths
    for p in ("/.netlify/ai/chat/completions", "/.netlify/ai/v1/chat/completions", "/.netlify/ai/providers"):
        st, b = api("POST", p, tok, {"provider": "anthropic", "model": "zz-no-such-model",
                                     "messages": [{"role": "user", "content": "hi"}]}, host=B_DOMAIN)
        print("subpath %-34s [%d] %s" % (p, st, b[:300].replace("\n", " ")), flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
