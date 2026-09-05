# -*- coding: utf-8 -*-
"""NL21: ai-gateway providers full list + baseline call without key (no real cost possible)"""
import http.client, ssl, json, sys, socket
sys.path.insert(0, r'F:\scan\netlify_report')
from _net_creds import TOKEN_B

ctx = ssl.create_default_context()
SITE_B_ID = 'd2977de0-d24d-4544-81cb-933e610cad7d'
B_DOMAIN = 'sec-b-08v4pk.netlify.app'


class V4Conn(http.client.HTTPSConnection):
    def connect(self):
        ip = socket.gethostbyname(self.host)
        self.sock = socket.create_connection((ip, self.port), self.timeout)
        self.sock = self._context.wrap_socket(self.sock, server_hostname=self.host)


def req(host, method, path, token=None, body=None):
    conn = V4Conn(host, 443, timeout=50, context=ctx)
    h = {'Host': host, 'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept': 'application/json'}
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
    print("== NL21 ==", flush=True)
    # full providers list (api.netlify.com, anon OK)
    st, b = req("api.netlify.com", "GET", "/api/v1/ai-gateway/providers")
    print("providers [%d]" % st, flush=True)
    try:
        j = json.loads(b)
        for name, meta in (j.get("providers") or {}).items():
            print("  %s: token_env=%s url_env=%s models=%s" % (
                name, meta.get("token_env_var"), meta.get("url_env_var"),
                (meta.get("models") or [])[:4]), flush=True)
    except Exception as e:
        print("parse fail", e, b[:300], flush=True)
    # token
    st, b = req("api.netlify.com", "GET", "/api/v1/sites/%s/ai-gateway/token" % SITE_B_ID, TOKEN_B)
    tok = json.loads(b).get("token")
    # baseline: real model, no key configured -> expect auth error from gateway/provider
    for pv, mdl in (("anthropic", "claude-sonnet-4-5"), ("gemini", "gemini-2.5-flash"),
                    ("openai", "gpt-4o")):
        body = {"provider": pv, "model": mdl, "messages": [{"role": "user", "content": "ping"}]}
        st, b = req(B_DOMAIN, "POST", "/.netlify/ai/", tok, body)
        print("%s/%s -> [%d] %s" % (pv, mdl, st, b[:350].replace("\n", " ")), flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
