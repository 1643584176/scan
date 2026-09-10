# -*- coding: utf-8 -*-
"""ET54: probe real webroutes/webapi search endpoints on www.zomato.com"""
import http.client, ssl, time

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0.0.0 Safari/537.36"

PATHS = [
    "/webroutes/search/autoSuggest?q=pizza",
    "/webapi/searchapi.php?q=pizza",
    "/webroutes/search/home",
]

def get(path):
    try:
        conn = http.client.HTTPSConnection("www.zomato.com", 443, timeout=15, context=ctx)
        conn.request("GET", path, headers={"User-Agent": UA,
                     "Accept": "application/json,text/html,*/*", "X-Hackerone": "xxbo"})
        r = conn.getresponse()
        raw = r.read(6000)
        conn.close()
        print("== %s -> %d ct=%s first=%d" % (path, r.status,
              r.headers.get("Content-Type", "-")[:40], len(raw)), flush=True)
        print("    " + raw.decode("utf-8", "replace")[:400].replace("\n", " "), flush=True)
    except Exception as e:
        print("== %s EXC %s" % (path, repr(e)[:110]), flush=True)

for p in PATHS:
    get(p)
    time.sleep(1.0)
print("done", flush=True)
