# -*- coding: utf-8 -*-
# _hk_verify_clean.py - verify all test hooks are gone
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_B

API = "https://api.netlify.com/api/v1"

def req(method, url):
    r = urllib.request.Request(url, method=method)
    r.add_header("Authorization", "Bearer " + TOKEN_B)
    try:
        with urllib.request.urlopen(r, timeout=20) as resp:
            return resp.status, None
    except urllib.error.HTTPError as e:
        b = e.read(2000)
        return e.code, b[:150]

all_ids = {}
for f in ("_hk_matrix2_ids.json", "_hk_ids2.txt", "_hk_matrix_ids.json"):
    try:
        if f.endswith(".json"):
            d = json.load(open(r"D:\scan\netlify_report\%s" % f))
        else:
            d = json.load(open(r"D:\scan\netlify_report\%s" % f))
        for k, v in d.items():
            all_ids[k] = v
    except Exception as ex:
        print(f, "read err:", ex)

# also list site hooks to catch any leftovers
s, hooks = req("GET", API + "/hooks?site_id=d2977de0-d24d-4544-81cb-933e610cad7d")
print("site hooks list status:", s)
if isinstance(hooks, list):
    print("remaining hooks:", [(h.get("id"), h.get("event"), h.get("data")) for h in hooks])
for k, hid in all_ids.items():
    s, b = req("GET", API + "/hooks/%s" % hid)
    print("hook %-6s %s -> %s %s" % (k, hid[:12], s, b or ""))
