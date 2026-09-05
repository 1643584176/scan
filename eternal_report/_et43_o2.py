# -*- coding: utf-8 -*-
"""ET43: o2_handler.php + make_payment_response.php param discovery"""
import http.client, ssl, time, re

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

def get(path, host="www.zomato.com"):
    try:
        conn = http.client.HTTPSConnection(host, 443, timeout=12, context=ctx)
        conn.request("GET", path, headers={"User-Agent": UA, "Accept": "application/json,text/html,*/*"})
        r = conn.getresponse()
        raw = r.read(6000)
        conn.close()
        print("[%s] -> %d ct=%s len=%d %s" % (path, r.status,
              r.headers.get("Content-Type", "-")[:24], len(raw),
              raw.decode("utf-8", "replace")[:220].replace("\n", " ")), flush=True)
    except Exception as e:
        print("[%s] EXC %s" % (path, repr(e)[:80]), flush=True)

# o2_handler param probes - ids only
for qs in ["?res_id=1", "?user_id=1", "?res_id=1&user_id=1",
           "?order_id=1", "?id=1", "?res_id=1&action=details"]:
    get("/php/o2_handler.php" + qs)
    time.sleep(1.1)

print("")
# payment response params
for qs in ["?order_id=1", "?payment_id=1", "?txn_id=1", "?id=1", "?order_id=1&status=success",
           "?orderid=1", "?razorpay_order_id=order_1"]:
    get("/payments_service/make_payment_response.php" + qs)
    time.sleep(1.1)

print("")
# zomaland pre_register - city param
for qs in ["?city=1", "?city_id=1", "?event_id=1", "?city=delhi"]:
    get("/ajax_handlers/zomaland/pre_register.php" + qs)
    time.sleep(1.1)
print("done", flush=True)
