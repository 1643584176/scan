# -*- coding: utf-8 -*-
"""ET60: parameter-name matrix on the 400 'error' query endpoints (no-session reachable)"""
import ssl, http.client, time, urllib.parse

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0.0.0 Safari/537.36"

TESTS = [
    ("/webroutes/restaurant/info", ["res_id=1", "resId=1", "restaurant_id=1", "id=1"]),
    ("/webroutes/reviews/loadMore", ["res_id=1", "resId=1", "restaurant_id=1"]),
    ("/webroutes/menu/viewMenu", ["res_id=1", "resId=1", "restaurant_id=1"]),
]

def get(path):
    try:
        conn = http.client.HTTPSConnection("www.zomato.com", 443, timeout=12, context=ctx)
        conn.request("GET", path, headers={"User-Agent": UA, "Accept": "application/json,*/*",
                     "X-Hackerone": "xxbo", "Referer": "https://www.zomato.com/ncr/restaurants?q=pizza"})
        r = conn.getresponse()
        raw = r.read(5000)
        conn.close()
        body = raw.decode("utf-8", "replace")[:170].replace("\n", " ")
        print("[%d] %-58s %s" % (r.status, path[:58], body), flush=True)
    except Exception as e:
        print("[EXC] %-58s %s" % (path[:58], repr(e)[:80]), flush=True)

for ep, params in TESTS:
    for pr in params:
        get(ep + "?" + pr)
        time.sleep(0.7)
print("done", flush=True)
