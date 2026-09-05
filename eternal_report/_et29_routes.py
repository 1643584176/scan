# -*- coding: utf-8 -*-
"""ET29: www.runnr.in Rails route discovery (low volume)"""
import http.client, ssl, time, re

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

PATHS = [
    "/login", "/sign_in", "/users/sign_in", "/signup", "/users/sign_up", "/logout",
    "/admin", "/admin/login", "/dashboard", "/home", "/app", "/orders", "/order",
    "/users", "/me", "/account", "/profile", "/settings", "/session",
    "/rider", "/riders", "/drivers", "/driver", "/fleet", "/fleets", "/partners",
    "/restaurants", "/vendors", "/merchants", "/delivery", "/deliveries", "/track",
    "/tracking", "/cities", "/search", "/explore", "/orders/new", "/order/new",
    "/api/orders", "/api/users", "/api/restaurants", "/api/riders", "/api/v1/orders",
    "/api/v1/users", "/internal", "/jobs", "/webhooks", "/health_check", "/up",
    "/assets", "/uploads", "/cable", "/graphql", "/admin/users", "/reports",
    "/dispatch", "/assignment", "/zones", "/slots", "/invoices", "/payments",
    "/settlements", "/wallets", "/transactions", "/coupons", "/promos",
]

def get(p):
    try:
        conn = http.client.HTTPSConnection("www.runnr.in", 443, timeout=10, context=ctx)
        conn.request("GET", p, headers={"User-Agent": UA, "Accept": "text/html,application/json,*/*",
                    "Accept-Language": "en-US,en;q=0.9"})
        r = conn.getresponse()
        raw = r.read(200000)
        conn.close()
        return r.status, raw
    except Exception as e:
        return -1, repr(e).encode()

hits = []
for p in PATHS:
    st, raw = get(p)
    body = raw.decode("utf-8", "replace")
    if st == 200:
        m = re.search(r"<title[^>]*>(.*?)</title>", body, re.S | re.I)
        t = m.group(1).strip()[:60] if m else body[:80].replace("\n", " ")
        ct = "json" if body[:1] in "[{\"" else "html"
        hits.append((p, st, ct, t))
        print("HIT %-28s [%d] %s %s" % (p, st, ct, t), flush=True)
    elif st not in (404, 403):
        print("ODD %-28s [%d] %s" % (p, st, body[:80].replace("\n", " ")), flush=True)
    time.sleep(0.8)
print("total hits: %d" % len(hits), flush=True)
print("done", flush=True)
