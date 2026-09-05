# -*- coding: utf-8 -*-
"""ET20: searchapi.php parameter mapping"""
import http.client, ssl, json

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

CASES = [
    "?q=pizza&entity_id=1&entity_type=city",
    "?entity_id=1&entity_type=city",
    "?q=pizza",
    "?q=pizza&entity_id=1&entity_type=city&cuisines=82",
    "?entity_id=1&entity_type=city&sort=rating&order=desc",
    "?q=pizza&entity_id=1&entity_type=city&category=1",
    "?collection_id=1&entity_id=1&entity_type=city",
    "?establishment_type=1&entity_id=1&entity_type=city",
]

def get(p):
    conn = http.client.HTTPSConnection("www.zomato.com", 443, timeout=15, context=ctx)
    conn.request("GET", "/webapi/searchapi.php" + p, headers={"User-Agent": UA,
                "Accept": "application/json", "X-Requested-With": "XMLHttpRequest"})
    r = conn.getresponse()
    raw = r.read(3000000)
    conn.close()
    return r.status, raw

for p in CASES:
    st, raw = get(p)
    body = raw.decode("utf-8", "replace")
    try:
        d = json.loads(body)
        res = d.get("results", {})
        rests = res.get("restaurants", {})
        n = "?"
        if isinstance(rests, dict):
            n = "keys=%s len=%d" % (list(rests.keys())[:8], len(json.dumps(rests)))
            if "data" in rests or "restaurants" in rests:
                inner = rests.get("data") or rests.get("restaurants")
                n += " inner=%d" % len(inner) if isinstance(inner, list) else ""
        elif isinstance(rests, list):
            n = "list=%d" % len(rests)
        msg = d.get("results", {}).get("common", {}).get("msg", "")
        print("%-85s [%d] rests: %s msg=%s" % (p, st, n, str(msg)[:60]), flush=True)
    except Exception as e:
        print("%-85s [%d] EXC %s body=%s" % (p, st, repr(e)[:60], body[:150]), flush=True)
print("done", flush=True)
