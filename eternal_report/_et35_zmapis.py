# -*- coding: utf-8 -*-
"""ET35: access.zomans.com api/v1 anonymous probing (login/forgetuser/pwdpolicy/authstatus)"""
import http.client, ssl, json, time

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

def req(method, path, body=None, hdr=None):
    conn = http.client.HTTPSConnection("access.zomans.com", 443, timeout=12, context=ctx)
    h = {"User-Agent": UA, "Accept": "application/json", "Content-Type": "application/json"}
    if hdr:
        h.update(hdr)
    conn.request(method, path, body=body, headers=h)
    r = conn.getresponse()
    raw = r.read(8000)
    conn.close()
    print("[%s %s] -> %d %s" % (method, path, r.status, r.reason), flush=True)
    try:
        j = json.loads(raw)
        print("   json:", json.dumps(j)[:500], flush=True)
    except Exception:
        print("   raw:", raw[:300].decode("utf-8", "replace"), flush=True)
    return r.status

# 1. config endpoints
for p in ["/api/v1/pwdpolicy", "/api/v1/authstatus", "/api/v1/config/layout", "/api/v1/eaac/config",
          "/api/v1/login", "/token"]:
    req("GET", p)
    time.sleep(0.7)

# 2. forgetuser - username recovery behavior (empty body)
req("POST", "/api/v1/forgetuser", json.dumps({}))
time.sleep(0.7)
req("POST", "/api/v1/forgetuser", json.dumps({"user": "nonexistent_user_zz9"}))
time.sleep(1)
print("done", flush=True)
