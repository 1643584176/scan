# -*- coding: utf-8 -*-
"""ET22: inspect searchapi.php restaurant element structure"""
import http.client, ssl, json

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

conn = http.client.HTTPSConnection("www.zomato.com", 443, timeout=15, context=ctx)
conn.request("GET", "/webapi/searchapi.php?q=pizza&entity_id=1&entity_type=city", headers={
    "User-Agent": UA, "Accept": "application/json", "X-Requested-With": "XMLHttpRequest"})
r = conn.getresponse()
raw = r.read(3000000)
conn.close()
d = json.loads(raw.decode("utf-8", "replace"))
res = d.get("results", {})
print("results keys:", list(res.keys()))
rests = res.get("restaurants")
print("restaurants type:", type(rests).__name__)
if isinstance(rests, list) and rests:
    print("element0:", json.dumps(rests[0])[:800])
    print("element5:", json.dumps(rests[5])[:400])
print("\ncommon:", json.dumps(res.get("common", {}))[:600])
print("\nrestaurant count keys:", json.dumps({k: v for k, v in res.items() if k != 'restaurants' and not isinstance(v, (dict, list))})[:500])
# raw tail around restaurants
s = raw.decode("utf-8", "replace")
i = s.find('"restaurants"')
print("\nRAW around restaurants:", s[i:i+400])
print("done", flush=True)
