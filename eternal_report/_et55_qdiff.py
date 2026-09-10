# -*- coding: utf-8 -*-
"""ET55: q-parameter differential on real searchapi.php (baseline semantics)"""
import http.client, ssl, time, json

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0.0.0 Safari/537.36"

PATHS = [
    "/webapi/searchapi.php?q=pizza",
    "/webapi/searchapi.php?q=sushi",
    "/webapi/searchapi.php?q=",
    "/webapi/searchapi.php",
]

def get(path):
    try:
        conn = http.client.HTTPSConnection("www.zomato.com", 443, timeout=15, context=ctx)
        conn.request("GET", path, headers={"User-Agent": UA,
                     "Accept": "application/json,text/html,*/*", "X-Hackerone": "xxbo"})
        r = conn.getresponse()
        raw = r.read(400000)
        conn.close()
        body = raw.decode("utf-8", "replace")
        line = "== %s -> %d len=%d" % (path, r.status, len(raw))
        try:
            d = json.loads(body)
            res = d.get("results", {})
            keys = list(res.keys()) if isinstance(res, dict) else type(res).__name__
            sect = None
            if isinstance(res, dict):
                for k in ("restaurants", "sections", "SECTION_RESTAURANT", "nearby_restaurants", "search_results"):
                    if k in res:
                        sect = (k, len(res[k]) if hasattr(res[k], "__len__") else res[k])
                        break
                top = res.get("results") if "results" in res else None
            print(line + " keys=%s sect=%s" % (keys if isinstance(keys, list) else keys, sect), flush=True)
        except Exception as e:
            print(line + " (non-json: %s)" % repr(e)[:60], flush=True)
        print("    " + body[:300].replace("\n", " "), flush=True)
        open("_et55_" + path.replace("/", "_").replace("?", "_").replace("=", "_")[:60] + ".json", "w", encoding="utf-8").write(body)
    except Exception as e:
        print("== %s EXC %s" % (path, repr(e)[:110]), flush=True)

for p in PATHS:
    get(p)
    time.sleep(1.0)
print("done", flush=True)
