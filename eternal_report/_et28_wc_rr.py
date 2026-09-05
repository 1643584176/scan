# -*- coding: utf-8 -*-
"""ET28: winecellar access variants + runnr gateway header probing"""
import http.client, ssl, time

ctx = ssl.create_default_context()
UA_C = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

def get(h, p, headers, read=80000):
    try:
        conn = http.client.HTTPSConnection(h, 443, timeout=12, context=ctx)
        conn.request("GET", p, headers=headers)
        r = conn.getresponse()
        raw = r.read(read)
        conn.close()
        h2 = dict((k.lower(), v) for k, v in r.getheaders())
        return r.status, h2, raw
    except Exception as e:
        return -1, {}, repr(e).encode()

print("== winecellar.zomato.com variants ==")
variants = [
    ("chrome", "/", {"User-Agent": UA_C, "Accept": "text/html,*/*"}),
    ("googlebot", "/", {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)", "Accept": "text/html"}),
    ("curl", "/", {"User-Agent": "curl/8.4.0", "Accept": "*/*"}),
    ("chrome-xff", "/", {"User-Agent": UA_C, "X-Forwarded-For": "49.207.0.0"}),
    ("robots", "/robots.txt", {"User-Agent": UA_C}),
    ("http10", "/", {"User-Agent": UA_C}),
]
for tag, p, hdrs in variants:
    st, h2, raw = get("winecellar.zomato.com", p, hdrs)
    print("%-12s %-14s [%d] srv=%s ct=%s len=%d body=%s" % (tag, p, st, h2.get("server", "-"), h2.get("content-type", "-")[:20], len(raw), raw[:120].decode("utf-8", "replace").replace("\n", " ")), flush=True)
    time.sleep(1)

print("\n== www.runnr.in gateway headers ==")
hdrsets = [
    ("plain", {"User-Agent": UA_C, "Accept": "application/json"}),
    ("x-requested-with", {"User-Agent": UA_C, "X-Requested-With": "XMLHttpRequest"}),
    ("x-access-token", {"User-Agent": UA_C, "X-Access-Token": "abc"}),
    ("authorization", {"User-Agent": UA_C, "Authorization": "Bearer abc"}),
    ("accept-all", {"User-Agent": UA_C, "Accept": "*/*", "Accept-Language": "en-US,en;q=0.9"}),
]
for tag, hdrs in hdrsets:
    st, h2, raw = get("www.runnr.in", "/", hdrs)
    print("%-16s [%d] srv=%s ct=%s len=%d body=%s" % (tag, st, h2.get("server", "-"), h2.get("content-type", "-")[:25], len(raw), raw[:150].decode("utf-8", "replace").replace("\n", " ")), flush=True)
    time.sleep(1)

print("\n== runnr path probes ==")
for p in ["/api", "/api/v1", "/health", "/robots.txt", "/favicon.ico", "/v1", "/status"]:
    st, h2, raw = get("www.runnr.in", p, {"User-Agent": UA_C, "Accept": "*/*"})
    print("%-16s [%d] ct=%s len=%d body=%s" % (p, st, h2.get("content-type", "-")[:25], len(raw), raw[:100].decode("utf-8", "replace").replace("\n", " ")), flush=True)
    time.sleep(1)
print("done", flush=True)
