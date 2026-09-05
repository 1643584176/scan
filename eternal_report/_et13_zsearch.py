# -*- coding: utf-8 -*-
"""ET13: Zomato public search page structure (SSR data / params) — no account needed"""
import http.client, ssl, re, json

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

def get(h, path, maxread=3000000):
    conn = http.client.HTTPSConnection(h, 443, timeout=20, context=ctx)
    conn.request("GET", path, headers={"User-Agent": UA, "Accept": "text/html,application/json,*/*",
                "Accept-Language": "en-US,en;q=0.9"})
    r = conn.getresponse()
    raw = r.read(maxread)
    conn.close()
    return r.status, dict((k.lower(), v) for k, v in r.getheaders()), raw

# try: NCR restaurants search page (public)
for path in ["/ncr/restaurants?q=pizza", "/ncr", "/search?q=pizza"]:
    st, hdrs, raw = get("www.zomato.com", path)
    body = raw.decode("utf-8", "replace")
    print("== %s [%d] len=%d ct=%s srv=%s" % (path, st, len(raw), hdrs.get("content-type", "")[:30], hdrs.get("server", "-")), flush=True)
    # next data?
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', body, re.S)
    if m:
        try:
            d = json.loads(m.group(1))
            print("NEXT buildId=%s page=%s" % (d.get("buildId"), d.get("page")), flush=True)
            # walk props for entity/query data
            pp = d.get("props", {}).get("pageProps", {})
            s = json.dumps(pp)
            print("pageProps len=%d keys=%s" % (len(s), list(pp.keys())[:25]), flush=True)
            open("_zomato_pp1.json", "w", encoding="utf-8").write(s)
        except Exception as e:
            print("next parse exc", repr(e)[:120], flush=True)
    else:
        # react shell? look for api urls inside
        apis = set(re.findall(r'["\'](https?://[^"\']*(?:api|search|restaurant)[^"\']*)["\']', body))
        for a in list(apis)[:20]:
            print("APIREF:", a[:150], flush=True)
        print("HTML head:", re.sub(r"\s+", " ", body[:600]), flush=True)
    print("", flush=True)
print("done", flush=True)
