# -*- coding: utf-8 -*-
"""ET31: zomans.com family — resolve + probe (admin.zomans.com from main.js)"""
import http.client, ssl, socket, time

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

def dns(h):
    try:
        return socket.gethostbyname(h)
    except Exception:
        return None

HOSTS = ["admin.zomans.com", "zomans.com", "www.zomans.com", "api.zomans.com",
         "internal.zomans.com", "dashboard.zomans.com", "app.zomans.com", "cms.zomans.com",
         "portal.zomans.com", "merchant.zomans.com", "db.zomans.com", "data.zomans.com",
         "analytics.zomans.com", "auth.zomans.com", "login.zomans.com", "pay.zomans.com"]

print("== zomans DNS ==")
alive = []
for h in HOSTS:
    ip = dns(h)
    if ip:
        alive.append(h)
        print("%-24s %s" % (h, ip), flush=True)
    time.sleep(0.1)

print("\n== probe alive ==")
for h in alive:
    try:
        conn = http.client.HTTPSConnection(h, 443, timeout=10, context=ctx)
        conn.request("GET", "/", headers={"User-Agent": UA, "Accept": "text/html,application/json,*/*"})
        r = conn.getresponse()
        raw = r.read(60000)
        conn.close()
        h2 = dict((k.lower(), v) for k, v in r.getheaders())
        body = raw.decode("utf-8", "replace")
        import re
        m = re.search(r"<title[^>]*>(.*?)</title>", body, re.S | re.I)
        t = m.group(1).strip()[:60] if m else (body[:90].replace("\n", " ") if body else "")
        print("%-24s [%d] srv=%s ct=%s len=%d %s" % (h, r.status, h2.get("server", "-")[:18], h2.get("content-type", "-")[:24], len(raw), t), flush=True)
    except Exception as e:
        print("%-24s EXC %s" % (h, repr(e)[:80]), flush=True)
print("done", flush=True)
