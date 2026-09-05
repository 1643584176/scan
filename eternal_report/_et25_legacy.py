# -*- coding: utf-8 -*-
"""ET25: probe legacy php handler + dining-gw res_id numeric surface (cool-off from www WAF)"""
import http.client, ssl, json, time

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

def get(h, p, read=1000000):
    conn = http.client.HTTPSConnection(h, 443, timeout=15, context=ctx)
    conn.request("GET", p, headers={"User-Agent": UA, "Accept": "application/json, text/plain, */*",
                "X-Requested-With": "XMLHttpRequest"})
    r = conn.getresponse()
    raw = r.read(read)
    conn.close()
    return r.status, raw

# 1. legacy php handlers on www (1-2 probes only, path may bypass IP block if path-level)
print("== legacy php ==")
for p in ["/webapi/handlers/Search/index.php?q=delhi", "/webapi/handlers/Search/index.php",
          "/webapi/searchapi.php?q=test&entity_id=1&entity_type=city&meta=1"]:
    st, raw = get("www.zomato.com", p)
    body = raw.decode("utf-8", "replace")[:180].replace("\n", " ")
    print("%-60s [%d] %s" % (p, st, body), flush=True)
    time.sleep(2)

# 2. api.zomato.com dining-gw: res_id numeric probes (different WAF stack?)
print("\n== api.zomato.com dining-gw res_id ==")
for p in ["/dining-gw/consumer/web/tr/slots?restaurant_id=1",
          "/dining-gw/consumer/web/tr/slots?res_id=1",
          "/dining-gw/consumer/web/tr/slots?restaurant_id=1&date=2026-09-05",
          "/dining-gw/consumer/web/restaurant/info?restaurant_id=1"]:
    st, raw = get("api.zomato.com", p)
    body = raw.decode("utf-8", "replace")[:200].replace("\n", " ")
    print("%-70s [%d] %s" % (p, st, body), flush=True)
    time.sleep(1.5)

# 3. api.zomato.com base behaviors
print("\n== api.zomato.com base ==")
for p in ["/", "/v2/get_masked_number.json", "/dining-gw/consumer/web/tr/slots?restaurant_id=abc"]:
    st, raw = get("api.zomato.com", p)
    body = raw.decode("utf-8", "replace")[:200].replace("\n", " ")
    print("%-60s [%d] %s" % (p, st, body), flush=True)
    time.sleep(1.5)
print("done", flush=True)
