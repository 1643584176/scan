# -*- coding: utf-8 -*-
"""ET42: searchapi.php param mapping — full default response + entity params"""
import http.client, ssl, json, time

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

def get(path):
    conn = http.client.HTTPSConnection("www.zomato.com", 443, timeout=15, context=ctx)
    conn.request("GET", path, headers={"User-Agent": UA, "Accept": "application/json"})
    r = conn.getresponse()
    raw = r.read()
    conn.close()
    return r.status, raw

# 1. full default structure
st, raw = get("/webapi/searchapi.php")
print("default:", st, len(raw))
try:
    j = json.loads(raw)
    print(json.dumps(j, indent=1)[:3500])
except Exception:
    print(raw[:800].decode("utf-8", "replace"))
print("====", flush=True)
time.sleep(1)

# 2. param experiments (numeric/id only, no SQL keywords)
for qs in ["?entity_type=city&entity_id=1",
           "?entity_id=1",
           "?category=1",
           "?q=pizza",
           "?collection_id=1",
           "?res_id=1"]:
    st, raw = get("/webapi/searchapi.php" + qs)
    b = raw.decode("utf-8", "replace")
    print("[%s] %d len=%d head=%s" % (qs, st, len(raw), b[:150].replace("\n", " ")), flush=True)
    time.sleep(1.0)
print("done", flush=True)
