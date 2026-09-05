# -*- coding: utf-8 -*-
"""NL20: force IPv4 to site domain to pass ai-gateway source-IP check"""
import http.client, ssl, json, sys, socket
sys.path.insert(0, r'F:\scan\netlify_report')
from _net_creds import TOKEN_B

ctx = ssl.create_default_context()
SITE_B_ID = 'd2977de0-d24d-4544-81cb-933e610cad7d'
B_DOMAIN = 'sec-b-08v4pk.netlify.app'


class V4Conn(http.client.HTTPSConnection):
    """TCP over IPv4 only, TLS SNI + cert check with real hostname"""
    def connect(self):
        ip = socket.gethostbyname(self.host)
        self.sock = socket.create_connection((ip, self.port), self.timeout)
        self.sock = self._context.wrap_socket(self.sock, server_hostname=self.host)


def resolve(host):
    try:
        infos = socket.getaddrinfo(host, 443, socket.AF_UNSPEC, socket.SOCK_STREAM)
        return [(i[0].name, i[4][0]) for i in infos]
    except Exception as e:
        return [('ERR', repr(e)[:80])]


def api_ipv4(host, path, token=None, body=None, method="POST"):
    """connect over IPv4, real Host header + SNI"""
    conn = V4Conn(host, 443, timeout=40, context=ctx)
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
    print("== NL20 ==", flush=True)
    # fetch token over IPv4
    st, b = api_ipv4("api.netlify.com", "/api/v1/sites/%s/ai-gateway/token" % SITE_B_ID, TOKEN_B, method="GET")
    print("token via ipv4 [%d] %s" % (st, b[:150]), flush=True)
    try:
        tok = json.loads(b).get("token")
    except Exception:
        return
    # POST to site domain over IPv4
    body = {"provider": "anthropic", "model": "zz-no-such-model",
            "messages": [{"role": "user", "content": "hi"}]}
    st, b = api_ipv4(B_DOMAIN, "/.netlify/ai/", tok, body)
    print("POST /.netlify/ai/ via ipv4 [%d] %s" % (st, b[:400].replace("\n", " ")), flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
