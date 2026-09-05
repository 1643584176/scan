# -*- coding: utf-8 -*-
"""ET18: probe zomato webroutes endpoints anonymously (GET only, low volume)"""
import http.client, ssl, re, json

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

TESTS = [
    ("www.zomato.com", "/webroutes/search/autoSuggest?q=pizza"),
    ("www.zomato.com", "/webroutes/search/home"),
    ("www.zomato.com", "/webroutes/search/applyFilter"),
    ("www.zomato.com", "/webroutes/location/search?q=delhi"),
    ("www.zomato.com", "/webapi/searchapi.php"),
    ("www.zomato.com", "/webapi/searchapi.php?q=pizza"),
    ("api.zomato.com", "/dining-gw/consumer/web/tr/slots"),
    ("api.zomato.com", "/gw/web/user/notification_preferences"),
    ("api.zomato.com", "/v2/get_masked_number.json"),
    ("api.eks.zdev.net", "/"),
]

def probe(h, p):
    try:
        conn = http.client.HTTPSConnection(h, 443, timeout=12, context=ctx)
        conn.request("GET", p, headers={"User-Agent": UA,
                    "Accept": "application/json, text/html, */*;q=0.8",
                    "X-Requested-With": "XMLHttpRequest"})
        r = conn.getresponse()
        raw = r.read(8000)
        conn.close()
        hdrs = dict((k.lower(), v) for k, v in r.getheaders())
        body = raw.decode("utf-8", "replace")[:250].replace("\n", " ")
        print("%-20s %-52s [%d] ct=%s srv=%s\n   %s" % (h, p, r.status,
              hdrs.get("content-type", "-")[:28], hdrs.get("server", "-")[:18], body), flush=True)
    except Exception as e:
        print("%-20s %-52s EXC %s" % (h, p, repr(e)[:90]), flush=True)

for h, p in TESTS:
    probe(h, p)
print("\n== __PRELOADED_STATE__ head ==")
try:
    body = open("_zomato_search.html", encoding="utf-8", errors="replace").read()
    m = re.search(r'<script[^>]*>window\.__PRELOADED_STATE__\s*=\s*(.*?)</script>', body, re.S)
    if m:
        s = m.group(1).strip()
        if s.endswith(";"):
            s = s[:-1]
        print("len=%d" % len(s))
        print(s[:1500])
        open("_zomato_state.json", "w", encoding="utf-8").write(s)
except Exception as e:
    print("state exc", repr(e)[:100])
print("done", flush=True)
