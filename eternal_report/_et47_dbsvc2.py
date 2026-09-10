# -*- coding: utf-8 -*-
"""ET47: remaining DB-ish subdomains (HTTP) + raw TCP port check for pg.ticketnew.com (handshake only)"""
import http.client, ssl, socket, time, re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

HTTP_TARGETS = [
    ("grafana.grofers.com", "/login"),
    ("superset.grofer.io", "/login/"),
    ("reports.grofer.io", "/"),
    ("internal.grofer.io", "/"),
    ("admin.district.in", "/"),
    ("admin.edition.in", "/"),
    ("admin.insider.in", "/"),
    ("api2.blinkit.com", "/"),
    ("api3.blinkit.com", "/"),
]

def probe(host, path):
    try:
        conn = http.client.HTTPSConnection(host, 443, timeout=15, context=ctx)
        conn.request("GET", path, headers={"User-Agent": UA,
                     "Accept": "text/html,application/json,*/*", "X-Hackerone": "xxbo"})
        r = conn.getresponse()
        raw = r.read(3000)
        conn.close()
        loc = r.headers.get("Location", "-")
        print("[%s%s] -> %d loc=%s ct=%s len=%d" % (host, path, r.status,
              loc[:75], r.headers.get("Content-Type", "-")[:28], len(raw)), flush=True)
        txt = re.sub(r"\s+", " ", raw.decode("utf-8", "replace"))[:170]
        print("    " + txt, flush=True)
    except Exception as e:
        print("[%s%s] EXC %s" % (host, path, repr(e)[:100]), flush=True)

def tcp(host, port):
    try:
        s = socket.create_connection((host, port), timeout=8)
        s.close()
        print("[TCP %s:%d] OPEN" % (host, port), flush=True)
    except Exception as e:
        print("[TCP %s:%d] closed/filtered (%s)" % (host, port, type(e).__name__), flush=True)

for h, p in HTTP_TARGETS:
    probe(h, p)
    time.sleep(1.0)

print("---- TCP ports ----", flush=True)
for port in (80, 443, 5432):
    tcp("pg.ticketnew.com", port)
print("done", flush=True)
