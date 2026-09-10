# -*- coding: utf-8 -*-
"""ET45: probe real API routes harvested from JS bundles (GET only, low volume)"""
import http.client, ssl, time

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

TARGETS = [
    ("www.district.in", "/web/search?q=pizza"),
    ("www.district.in", "/consumer/events/v1/event/getBySlug?slug=x"),
    ("www.district.in", "/movies/fetchCinemasNearMe"),
    ("api-internal.edition.in", "/gw"),
    ("www.zomato.com", "/web/search?q=pizza"),
    ("www.district.in", "/ext/payment-link"),
]

def probe(host, path, ref):
    try:
        conn = http.client.HTTPSConnection(host, 443, timeout=12, context=ctx)
        conn.request("GET", path, headers={"User-Agent": UA,
                     "Accept": "application/json,text/html,*/*",
                     "X-Hackerone": "xxbo", "Referer": ref})
        r = conn.getresponse()
        raw = r.read(3000)
        conn.close()
        print("[%s%s] -> %d ct=%s len=%d %s" % (host, path[:60], r.status,
              r.headers.get("Content-Type", "-")[:24], len(raw),
              raw.decode("utf-8", "replace")[:160].replace("\n", " ")), flush=True)
    except Exception as e:
        print("[%s%s] EXC %s" % (host, path[:60], repr(e)[:90]), flush=True)

for h, p in TARGETS:
    ref = "https://www.zomato.com/" if "zomato" in h else "https://www.district.in/"
    probe(h, p, ref)
    time.sleep(1.0)
print("done", flush=True)
