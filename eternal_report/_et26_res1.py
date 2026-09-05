# -*- coding: utf-8 -*-
"""ET26: full res_id=1 response + numeric arithmetic probe (SQLi detection via eval)"""
import http.client, ssl, json, time, hashlib

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

def get(p, read=3000000):
    conn = http.client.HTTPSConnection("api.zomato.com", 443, timeout=15, context=ctx)
    conn.request("GET", "/dining-gw/consumer/web/tr/slots" + p, headers={"User-Agent": UA,
                "Accept": "application/json", "X-Requested-With": "XMLHttpRequest"})
    r = conn.getresponse()
    raw = r.read(read)
    conn.close()
    return r.status, raw

# 1. full structure of res_id=1
st, raw = get("?res_id=1")
body = raw.decode("utf-8", "replace")
print("res_id=1 [%d] len=%d" % (st, len(raw)))
d = json.loads(body)
print(json.dumps(d, indent=1)[:2500])
print("done", flush=True)
