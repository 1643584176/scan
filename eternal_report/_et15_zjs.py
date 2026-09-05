# -*- coding: utf-8 -*-
"""ET15: dl zomato key bundles (main/Search/uniSearch) + grep endpoints"""
import http.client, ssl, re, os, json

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_js")

BUNDLES = [
    "main-8efa4cf644fa76389041.js",
    "pages-Search-19402afa43cd46f9047b.js",
    "layoutEntries-uniSearchDesContainer-a105a76fa4d68a81add7.js",
    "layoutEntries-searchDesktopIndex-dc423479412fc1cc3c30.js",
    "zomato-5b4c68bb1f2c1592a059.js",
    "RestaurantCardV2-8514e8764c02f001f2ae.js",
]

def get(h, path, maxread=6000000):
    conn = http.client.HTTPSConnection(h, 443, timeout=30, context=ctx)
    conn.request("GET", path, headers={"User-Agent": UA, "Accept": "*/*"})
    r = conn.getresponse()
    raw = r.read(maxread)
    conn.close()
    return r.status, raw

for b in BUNDLES:
    fn = os.path.join(OUT, "z_" + b)
    if os.path.exists(fn) and os.path.getsize(fn) > 2000:
        continue
    st, raw = get("zwstatic.zomato.com", "/" + b)
    if st == 200:
        open(fn, "wb").write(raw)
        print("saved %s (%d KB)" % (b, len(raw) // 1024), flush=True)
    else:
        print("fail %s [%d]" % (b, st), flush=True)

# grep endpoints
print("\n== api endpoints in zomato bundles ==")
endp = {}
for b in BUNDLES:
    fn = os.path.join(OUT, "z_" + b)
    if not os.path.exists(fn):
        continue
    data = open(fn, encoding="utf-8", errors="replace").read()
    for m in re.finditer(r'["\'](/[a-zA-Z0-9_\-./]{4,120}?)(?:["\']|`|\?)', data):
        p = m.group(1)
        if any(k in p for k in ("/api/", "/search", "/restaurant", "/v1", "/v2", "/v3", "collection",
                                 "discovery", "autocomplete", "geocode", "location", "reviews", "dining",
                                 "order", "user", "menu", "delivery", "listing", "suggest", "explore")):
            endp.setdefault(p[:120], set()).add(b)
for p in sorted(endp):
    print("%-100s %s" % (p, ",".join(sorted(endp[p]))))
print("done", flush=True)
