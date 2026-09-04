# -*- coding: utf-8 -*-
# _ar_recon3_full.py - full dump of token identity run session
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_B

API = "https://api.netlify.com/api/v1"
RID = "6a98db3f0041c71a1811ee8d"
SID = "6a98db3f0041c71a1811ee8f"

def req(method, url, tok=None, timeout=40):
    r = urllib.request.Request(url, method=method)
    if tok:
        r.add_header("Authorization", "Bearer " + tok)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            b = resp.read(300000)
            try:
                return resp.status, json.loads(b.decode("utf-8", "replace"))
            except Exception:
                return resp.status, b[:3000]
    except urllib.error.HTTPError as e:
        return e.code, e.read(3000)[:2000]
    except Exception as ex:
        return -1, str(ex)[:300]

s, d = req("GET", API + "/agent_runners/%s/sessions/%s" % (RID, SID), tok=TOKEN_B)
print("single session:", s)
if isinstance(d, dict):
    print("keys:", list(d.keys()))
    print(json.dumps({k: v for k, v in d.items() if k != "result"}, ensure_ascii=False, indent=1)[:4000])
    res = d.get("result")
    print("\nresult type:", type(res).__name__)
    if isinstance(res, dict):
        print("result keys:", list(res.keys()))
        print(json.dumps(res, ensure_ascii=False)[:12000])
    else:
        print(str(res)[:4000])
else:
    print(d)
