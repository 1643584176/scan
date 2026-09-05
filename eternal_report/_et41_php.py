# -*- coding: utf-8 -*-
"""ET41: probe legacy php + internal endpoints on www.zomato.com (GET only, no payloads)"""
import http.client, ssl, time, re

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

def probe(path, host="www.zomato.com"):
    try:
        conn = http.client.HTTPSConnection(host, 443, timeout=12, context=ctx)
        conn.request("GET", path, headers={"User-Agent": UA, "Accept": "application/json,text/plain,*/*"})
        r = conn.getresponse()
        raw = r.read(6000)
        conn.close()
        b = raw.decode("utf-8", "replace")[:200].replace("\n", " ")
        print("[%s] -> %d ct=%s len=%d %s" % (path, r.status,
              r.headers.get("Content-Type", "-")[:26], len(raw), b), flush=True)
    except Exception as e:
        print("[%s] EXC %s" % (path, repr(e)[:80]), flush=True)

PATHS = [
    "/php/o2_handler.php",
    "/payments_service/make_payment_response.php",
    "/php/zomaland/make_payment.php",
    "/php/zomaland/payment_handler.php",
    "/ajax_handlers/zomaland/pre_register.php",
    "/php/reportErrorHandler.php",
    "/php/chat_auth_handler.php",
    "/gw/internal/auth/validate",
    "/webapi/handlers/Search/index.php",
    "/webapi/searchapi.php",
    "/webroutes/auth/csrf",
    "/webroutes/search/home",
    "/webroutes/search/autoSuggest",
]
for p in PATHS:
    probe(p)
    time.sleep(1.0)

print("\n== external.zomans.com ==")
probe("/", "external.zomans.com")
time.sleep(1)
probe("/health", "external.zomans.com")
print("done", flush=True)
