# -*- coding: utf-8 -*-
"""ET56: extract script srcs from search page html + POST form test on searchapi.php"""
import re, os, http.client, ssl, time

HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_zomato_search.html")
data = open(HTML, "r", encoding="utf-8", errors="replace").read()
print("html len:", len(data), flush=True)
srcs = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', data)
print("== script srcs (%d) ==" % len(srcs), flush=True)
have = set(os.listdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_js")))
for s in srcs:
    print(" ", s[:160], flush=True)
pre = sorted(set(re.findall(r'window\.__[A-Za-z_]+', data)))
print("== window vars ==", pre[:30], flush=True)

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0.0.0 Safari/537.36"

def req(method, path, body=None, ctype=None):
    hdr = {"User-Agent": UA, "Accept": "application/json,text/html,*/*", "X-Hackerone": "xxbo",
           "Referer": "https://www.zomato.com/"}
    if ctype:
        hdr["Content-Type"] = ctype
    conn = http.client.HTTPSConnection("www.zomato.com", 443, timeout=15, context=ctx)
    conn.request(method, path, body=body, headers=hdr)
    r = conn.getresponse()
    raw = r.read(30000)
    conn.close()
    print("== %s %s -> %d len>=%d" % (method, path, r.status, len(raw)), flush=True)
    print("    " + raw.decode("utf-8", "replace")[:260].replace("\n", " "), flush=True)

req("POST", "/webapi/searchapi.php", "q=pizza", "application/x-www-form-urlencoded")
time.sleep(1)
req("POST", "/webapi/searchapi.php", '{"q":"pizza"}', "application/json")
time.sleep(1)
req("GET", "/webapi/searchapi.php?q=pizza&city_id=1")
print("done", flush=True)
