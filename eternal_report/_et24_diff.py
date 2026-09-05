# -*- coding: utf-8 -*-
"""ET24: diff delhi vs delhi' responses; probe location/search params"""
import http.client, ssl, json, time, hashlib, difflib

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

r0 = get("?q=delhi")
r1 = get("?q=delhi'")
d0 = json.loads(r0[1].decode("utf-8", "replace"))
d1 = json.loads(r1[1].decode("utf-8", "replace"))
s0 = json.dumps(d0, sort_keys=True, indent=0)
s1 = json.dumps(d1, sort_keys=True, indent=0)
print("B0 len=%d B1 len=%d same=%s" % (len(s0), len(s1), s0 == s1))
# find which keys differ
l0 = d0.get("locationSuggestions", [])
l1 = d1.get("locationSuggestions", [])
for i in range(min(len(l0), len(l1))):
    if json.dumps(l0[i], sort_keys=True) != json.dumps(l1[i], sort_keys=True):
        # field-level diff
        a, b = l0[i], l1[i]
        for k in set(list(a.keys()) + list(b.keys())):
            if a.get(k) != b.get(k):
                print("idx %d key %s: B0=%r B1=%r" % (i, k, str(a.get(k))[:80], str(b.get(k))[:80]))
print("n0=%d n1=%d" % (len(l0), len(l1)))

# param surface probes
print("\n== param surface ==")
time.sleep(1)
for p in ["?q=%27", "?q=%22", "?q=", "?s=delhi", "?term=delhi", "?query=delhi",
          "?q=delhi&lat=28.6&lon=77.2", "?q=delhi&city_id=1", "?lat=28.6&lon=77.2"]:
    st, raw = get(p)
    body = raw.decode("utf-8", "replace")[:160].replace("\n", " ")
    print("%-38s [%d] %s" % (p, st, body), flush=True)
    time.sleep(1)
print("done", flush=True)
