# -*- coding: utf-8 -*-
"""ET24b: diff delhi vs delhi' with status checks; probe location/search params"""
import http.client, ssl, json, time

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

def parse(st, raw, tag):
    try:
        d = json.loads(raw.decode("utf-8", "replace"))
        return d
    except Exception:
        print("%s [%d] NOT-JSON: %s" % (tag, st, raw[:150].decode("utf-8", "replace")), flush=True)
        return None

r0 = get("?q=delhi")
time.sleep(1.5)
r1 = get("?q=delhi'")
d0 = parse(r0[0], r0[1], "B0")
d1 = parse(r1[0], r1[1], "B1")
if d0 is not None and d1 is not None:
    l0 = d0.get("locationSuggestions", [])
    l1 = d1.get("locationSuggestions", [])
    print("n0=%d n1=%d same_first=%s" % (len(l0), len(l1), json.dumps(l0[0], sort_keys=True) == json.dumps(l1[0], sort_keys=True) if l0 and l1 else "?"))
    for i in range(min(len(l0), len(l1))):
        a, b = l0[i], l1[i]
        if json.dumps(a, sort_keys=True) != json.dumps(b, sort_keys=True):
            for k in set(list(a.keys()) + list(b.keys())):
                if a.get(k) != b.get(k):
                    print("idx %d key %s: B0=%r B1=%r" % (i, k, str(a.get(k))[:90], str(b.get(k))[:90]))

print("\n== param surface ==")
for p in ["?q=%27", "?q=%22", "?q=", "?s=delhi", "?term=delhi", "?query=delhi",
          "?q=delhi&lat=28.6&lon=77.2", "?q=delhi&city_id=1", "?lat=28.6&lon=77.2"]:
    st, raw = get(p)
    body = raw.decode("utf-8", "replace")[:150].replace("\n", " ")
    print("%-38s [%d] %s" % (p, st, body), flush=True)
    time.sleep(1.5)
print("done", flush=True)
