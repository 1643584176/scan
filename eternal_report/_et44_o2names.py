# -*- coding: utf-8 -*-
"""ET44: o2_handler.php param-name matrix (GET only, ids, X-Hackerone header)"""
import http.client, ssl, time

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

def get(path):
    try:
        conn = http.client.HTTPSConnection("www.zomato.com", 443, timeout=12, context=ctx)
        conn.request("GET", path, headers={"User-Agent": UA, "Accept": "application/json,text/html,*/*", "X-Hackerone": "xxbo"})
        r = conn.getresponse()
        raw = r.read(4000)
        conn.close()
        print("[%s] -> %d %s" % (path, r.status, raw.decode("utf-8", "replace")[:220].replace("\n", " ")), flush=True)
    except Exception as e:
        print("[%s] EXC %s" % (path, repr(e)[:80]), flush=True)

names = ["resId", "resid", "ResId", "order_id", "orderId", "orderid",
         "oid", "id", "r_id", "u_id", "restaurant_id", "resid_id"]
for n in names:
    get("/php/o2_handler.php?" + n + "=1")
    time.sleep(1.0)
print("done", flush=True)
