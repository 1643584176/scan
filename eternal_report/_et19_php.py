# -*- coding: utf-8 -*-
"""ET19: full searchapi.php response + parameter surface mapping"""
import http.client, ssl, json, re

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

def get(p, maxread=3000000):
    conn = http.client.HTTPSConnection("www.zomato.com", 443, timeout=20, context=ctx)
    conn.request("GET", p, headers={"User-Agent": UA, "Accept": "application/json",
                "X-Requested-With": "XMLHttpRequest"})
    r = conn.getresponse()
    raw = r.read(maxread)
    conn.close()
    return r.status, raw

# full default response
st, raw = get("/webapi/searchapi.php")
print("no-param [%d] len=%d" % (st, len(raw)))
body = raw.decode("utf-8", "replace")
open("_searchapi_default.json", "w", encoding="utf-8").write(body)
try:
    d = json.loads(body)
    print("top keys:", list(d.keys()))
    res = d.get("results", {})
    print("results keys:", list(res.keys()))
    locs = res.get("locations", {})
    print("locations keys:", list(locs.keys()))
    city = locs.get("city", {})
    print("city:", json.dumps(city)[:600])
    # any sections/restaurant listing keys?
    def walk(o, path="", depth=0):
        if depth > 3:
            return
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, (dict, list)) and v:
                    walk(v, path + "/" + k, depth + 1)
                else:
                    if k in ("total_restaurants", "results_shown", "has_more", "num_results"):
                        print("COUNT-KEY %s=%r" % (path + "/" + k, v))
    walk(d)
except Exception as e:
    print("parse exc", repr(e)[:100])
    print(body[:2000])
print("done", flush=True)
