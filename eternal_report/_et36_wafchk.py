# -*- coding: utf-8 -*-
"""ET36: WAF cooldown check — www.zomato.com + api.zomato.com baseline"""
import http.client, ssl, time

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

def probe(host, path, extra=None):
    try:
        conn = http.client.HTTPSConnection(host, 443, timeout=12, context=ctx)
        h = {"User-Agent": UA, "Accept": "text/html,application/json,*/*"}
        if extra:
            h.update(extra)
        conn.request("GET", path, headers=h)
        r = conn.getresponse()
        raw = r.read(20000)
        conn.close()
        print("[%s%s] -> %d ct=%s len=%d %s" % (host, path, r.status,
              r.headers.get("Content-Type", "-")[:20], len(raw),
              raw[:80].decode("utf-8", "replace").replace("\n", " ")), flush=True)
    except Exception as e:
        print("[%s%s] EXC %s" % (host, path, repr(e)[:80]), flush=True)

probe("www.zomato.com", "/")
time.sleep(1.2)
probe("www.zomato.com", "/webroutes/location/search?q=delhi")
time.sleep(1.2)
probe("api.zomato.com", "/dining-gw/consumer/web/dining/reservation/tr/slots?res_id=1&date=2026-09-06&time=19:00&party_size=2")
print("done", flush=True)
