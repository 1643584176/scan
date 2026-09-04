# -*- coding: utf-8 -*-
# _ar_credit1.py - check remaining credits after run 3
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_B

API = "https://api.netlify.com/api/v1"

def req(method, url, tok=None, timeout=20):
    r = urllib.request.Request(url, method=method)
    if tok:
        r.add_header("Authorization", "Bearer " + tok)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            b = resp.read(20000)
            try:
                return resp.status, json.loads(b.decode("utf-8", "replace"))
            except Exception:
                return resp.status, b[:500]
    except urllib.error.HTTPError as e:
        return e.code, e.read(2000)[:500]

s, d = req("GET", API + "/6a97b6454fef0db964f75db6/agent_runner_credit_usage", tok=TOKEN_B)
print(s, json.dumps(d, ensure_ascii=False, indent=1) if isinstance(d, dict) else d)
# also list runs to see state
s, d = req("GET", API + "/agent_runners?site_id=d2977de0-d24d-4544-81cb-933e610cad7d&per_page=10", tok=TOKEN_B)
if isinstance(d, list):
    for r in d:
        print(r.get("id"), r.get("state"), r.get("title", "")[:40])
