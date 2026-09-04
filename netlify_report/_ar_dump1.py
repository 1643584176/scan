# -*- coding: utf-8 -*-
# _ar_dump1.py - full dump of agent runner detail
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_B

API = "https://api.netlify.com/api/v1"
RID = "6a98d5e6448c07a76d7babf3"

def req(method, url, tok=None, timeout=30):
    r = urllib.request.Request(url, method=method)
    if tok:
        r.add_header("Authorization", "Bearer " + tok)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        return e.code, e.read(4000)[:2000]

s, d = req("GET", API + "/agent_runners/%s" % RID, tok=TOKEN_B)
print("status:", s)
print(json.dumps(d, ensure_ascii=False, indent=1))
