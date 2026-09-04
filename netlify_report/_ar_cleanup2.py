# -*- coding: utf-8 -*-
# _ar_cleanup2.py - delete remaining agent runs + check dev servers
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_B

API = "https://api.netlify.com/api/v1"
SITE_B = "d2977de0-d24d-4544-81cb-933e610cad7d"
RIDS = ["6a98db3f0041c71a1811ee8d", "6a98da92968b9a6f212f9775", "6a98d6d818790895d7d5ac00"]

def req(method, url, tok=None, body=None, timeout=30):
    r = urllib.request.Request(url, method=method)
    if tok:
        r.add_header("Authorization", "Bearer " + tok)
    data = json.dumps(body).encode() if body is not None else None
    if body is not None:
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, data=data, timeout=timeout) as resp:
            b = resp.read(20000)
            try:
                return resp.status, json.loads(b.decode("utf-8", "replace"))
            except Exception:
                return resp.status, b[:300]
    except urllib.error.HTTPError as e:
        b = e.read(4000)
        try:
            return e.code, json.loads(b.decode("utf-8", "replace"))
        except Exception:
            return e.code, b[:300]
    except Exception as ex:
        return -1, str(ex)[:200]

for rid in RIDS:
    s, d = req("DELETE", API + "/agent_runners/%s" % rid, tok=TOKEN_B)
    if isinstance(d, bytes):
        d = d.decode("utf-8", "replace")
    print("DELETE", rid, "->", s, json.dumps(d, ensure_ascii=False)[:200] if not isinstance(d, str) else d[:200])

# verify gone
s, d = req("GET", API + "/agent_runners?site_id=%s&per_page=10" % SITE_B, tok=TOKEN_B)
print("\nremaining runs:", s)
if isinstance(d, list):
    for r in d:
        print(" ", r.get("id"), r.get("state"), (r.get("title") or "")[:40])
else:
    print(d)

# dev servers state after run deletion
s, d = req("GET", API + "/sites/%s/dev_servers?page=1&per_page=20" % SITE_B, tok=TOKEN_B)
print("\ndev servers:", s, json.dumps(d, ensure_ascii=False)[:800] if not isinstance(d, str) else d)
