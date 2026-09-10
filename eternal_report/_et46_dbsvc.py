# -*- coding: utf-8 -*-
"""ET46: probe DB/admin service subdomains found by ET12 (GET root only, no auth attempts)"""
import http.client, ssl, time, re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

TARGETS = [
    ("phpmyadmin.zomans.com", "/"),
    ("kibana.zomans.com", "/"),
    ("grafana.zomans.com", "/login"),
    ("superset.zomans.com", "/login/"),
    ("admin.zomans.com", "/"),
    ("pg.ticketnew.com", "/"),
]

def probe(host, path):
    try:
        conn = http.client.HTTPSConnection(host, 443, timeout=15, context=ctx)
        conn.request("GET", path, headers={"User-Agent": UA,
                     "Accept": "text/html,application/json,*/*", "X-Hackerone": "xxbo"})
        r = conn.getresponse()
        raw = r.read(4000)
        conn.close()
        loc = r.headers.get("Location", "-")
        print("[%s%s] -> %d loc=%s ct=%s len=%d" % (host, path, r.status,
              loc[:80], r.headers.get("Content-Type", "-")[:30], len(raw)), flush=True)
        txt = re.sub(r"\s+", " ", raw.decode("utf-8", "replace"))[:200]
        print("    " + txt, flush=True)
    except Exception as e:
        print("[%s%s] EXC %s" % (host, path, repr(e)[:110]), flush=True)

for h, p in TARGETS:
    probe(h, p)
    time.sleep(1.0)
print("done", flush=True)
