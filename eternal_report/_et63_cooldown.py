# -*- coding: utf-8 -*-
"""ET63: cooldown check - single normal request after WAF alert"""
import ssl, http.client, time

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0.0.0 Safari/537.36"

print("cooling down 60s before single baseline request...", flush=True)
time.sleep(60)

try:
    conn = http.client.HTTPSConnection("www.zomato.com", 443, timeout=15, context=ctx)
    conn.request("GET", "/webroutes/restaurant/info?res_id=3",
                 headers={"User-Agent": UA, "Accept": "application/json,*/*",
                          "X-Hackerone": "xxbo", "Referer": "https://www.zomato.com/ncr/restaurants?q=pizza"})
    r = conn.getresponse()
    raw = r.read(4000)
    conn.close()
    print("[%d len=%d] %s" % (r.status, len(raw), raw.decode("utf-8", "replace")[:160].replace("\n", " ")), flush=True)
except Exception as e:
    print("[EXC] %s" % repr(e)[:120], flush=True)
print("done", flush=True)
