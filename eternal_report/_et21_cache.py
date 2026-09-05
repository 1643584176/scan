# -*- coding: utf-8 -*-
"""ET21: check if searchapi.php responses are distinct (cache?) — compare restaurant ids"""
import http.client, ssl, json, time, hashlib

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

def get(p, extra_hdrs=None):
    conn = http.client.HTTPSConnection("www.zomato.com", 443, timeout=15, context=ctx)
    hdrs = {"User-Agent": UA, "Accept": "application/json", "X-Requested-With": "XMLHttpRequest"}
    if extra_hdrs:
        hdrs.update(extra_hdrs)
    conn.request("GET", "/webapi/searchapi.php" + p, headers=hdrs)
    r = conn.getresponse()
    raw = r.read(3000000)
    h2 = dict((k.lower(), v) for k, v in r.getheaders())
    conn.close()
    return r.status, h2, raw

CASES = [
    "?q=pizza&entity_id=1&entity_type=city",
    "?q=burger&entity_id=1&entity_type=city",
    "?entity_id=1&entity_type=city",
    "?q=zzqqxx_nonexistent&entity_id=1&entity_type=city",
]
for p in CASES:
    st, h2, raw = get(p)
    try:
        d = json.loads(raw.decode("utf-8", "replace"))
        rests = d.get("results", {}).get("restaurants", [])
        ids = [r.get("restaurant", {}).get("id") for r in rests] if isinstance(rests, list) else []
        names = [r.get("restaurant", {}).get("name", "")[:20] for r in rests][:5] if isinstance(rests, list) else []
        cf = h2.get("cf-cache-status", "-")
        age = h2.get("age", "-")
        print("%-48s [%d] cf=%s age=%s n=%d ids=%s" % (p, st, cf, age, len(ids), ids[:11]), flush=True)
        print("   names:", names, flush=True)
    except Exception as e:
        print("%s EXC %s" % (p, repr(e)[:80]), flush=True)
    time.sleep(1)
print("done", flush=True)
