# -*- coding: utf-8 -*-
"""ET30: runnr auth shape — 401 details + token/login endpoint hunt"""
import http.client, ssl, time, json

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

def req(method, p, headers=None, body=None):
    try:
        conn = http.client.HTTPSConnection("www.runnr.in", 443, timeout=10, context=ctx)
        hdrs = {"User-Agent": UA, "Accept": "application/json, text/html, */*",
                "Content-Type": "application/json"}
        if headers:
            hdrs.update(headers)
        conn.request(method, p, body=body, headers=hdrs)
        r = conn.getresponse()
        raw = r.read(300000)
        conn.close()
        h2 = dict((k.lower(), v) for k, v in r.getheaders())
        return r.status, h2, raw
    except Exception as e:
        return -1, {}, repr(e).encode()

# 1. 401 details on /orders
st, h2, raw = req("GET", "/orders")
print("/orders [%d] www=%s body=%s" % (st, h2.get("www-authenticate", "-"), raw[:200].decode("utf-8", "replace")), flush=True)
time.sleep(1)

# 2. token-ish header guesses on /orders
for hdr_name in ["X-Auth-Token", "X-API-Key", "X-Token", "Token", "access_token"]:
    st, h2, raw = req("GET", "/orders", {hdr_name: "abc"})
    print("/orders %s=abc [%d] body=%s" % (hdr_name, st, raw[:120].decode("utf-8", "replace")), flush=True)
    time.sleep(0.8)

# 3. login/session endpoint hunt (POST probes)
print("\n== login endpoint probes ==")
for p, body in [
    ("/api/v1/login", json.dumps({"phone": "9999999999", "password": "x"})),
    ("/api/v1/sessions", json.dumps({"phone": "9999999999", "password": "x"})),
    ("/api/v1/auth", json.dumps({})),
    ("/auth/login", json.dumps({})),
    ("/login.json", json.dumps({"username": "a", "password": "b"})),
    ("/api/v1/users/login", json.dumps({})),
]:
    st, h2, raw = req("POST", p, body=body)
    print("POST %-24s [%d] ct=%s body=%s" % (p, st, h2.get("content-type", "-")[:22], raw[:150].decode("utf-8", "replace").replace("\n", " ")), flush=True)
    time.sleep(1)
print("done", flush=True)
