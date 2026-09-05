# -*- coding: utf-8 -*-
"""ET14: analyze zomato search SSR page — state injection + js bundles"""
import http.client, ssl, re, json

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

conn = http.client.HTTPSConnection("www.zomato.com", 443, timeout=25, context=ctx)
conn.request("GET", "/ncr/restaurants?q=pizza", headers={"User-Agent": UA, "Accept": "text/html",
            "Accept-Language": "en-US,en;q=0.9"})
r = conn.getresponse()
raw = r.read(4000000)
body = raw.decode("utf-8", "replace")
conn.close()
print("len=%d" % len(raw), flush=True)
open("_zomato_search.html", "w", encoding="utf-8").write(body)

print("\n== state injection markers ==")
for m in re.finditer(r'<script[^>]*>(.{0,120}?(?:__|INITIAL|PRELOADED|STATE|APP_INITIAL|redux|window\.)[^<]{0,120})</script>', body):
    s = m.group(1).strip()
    if len(s) > 40 and "<" not in s:
        print("MARK:", s[:160].replace("\n", " "), flush=True)

print("\n== window.__ assignments ==")
for m in re.finditer(r'window\.([A-Za-z_$][A-Za-z0-9_$]{2,60})\s*=', body):
    print("  window.%s" % m.group(1), flush=True)

print("\n== script srcs ==")
srcs = []
for m in re.finditer(r'<script[^>]+src="([^"]+)"', body):
    u = m.group(1)
    if any(k in u for k in (".js", "_next", "static")):
        srcs.append(u)
        print("  ", u, flush=True)
print("total srcs:", len(srcs), flush=True)

print("\n== zomato api-ish hosts in page ==")
for m in sorted(set(re.findall(r'https?://([a-z0-9.\-]*zomato[a-z0-9.\-]*\.(?:com|in))[^"\']*', body))):
    print("  ", m, flush=True)

print("\n== interesting param patterns (res_id etc) ==")
for m in sorted(set(re.findall(r'[?&]([a-z_]{2,30})=(?:res_id|%7B|\d{5,})', body)))[:0] or []:
    pass
for m in sorted(set(re.findall(r'/restaurant\?[^"\']{0,80}', body)))[:8]:
    print("  ", m, flush=True)
print("done", flush=True)
