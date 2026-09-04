# -*- coding: utf-8 -*-
# _ds_probe2.py - B account credits + dev_servers attempt on SITE_B
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_B
import _net_creds as C

SITE_B = "d2977de0-d24d-4544-81cb-933e610cad7d"
API = "https://api.netlify.com/api/v1"

def req(method, url, tok=None, body=None, timeout=25):
    r = urllib.request.Request(url, method=method)
    if tok:
        r.add_header("Authorization", "Bearer " + tok)
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, data=data, timeout=timeout) as resp:
            b = resp.read(30000)
            try:
                return resp.status, json.loads(b.decode("utf-8", "replace"))
            except Exception:
                return resp.status, b[:500]
    except urllib.error.HTTPError as e:
        b = e.read(4000)
        try:
            return e.code, json.loads(b.decode("utf-8", "replace"))
        except Exception:
            return e.code, b[:400]
    except Exception as ex:
        return -1, str(ex)[:200]

# B account full - check credits fields
s, b = req("GET", API + "/accounts?minimal=false", tok=TOKEN_B)
if isinstance(b, list) and b:
    a = b[0]
    for k in ("slug", "id", "type", "type_id"):
        print(k, "=", a.get(k))
    for k in ("credits", "credit_balance", "blocked_by_orb_migration", "ai_usage_limit_credits"):
        if k in a:
            print(k, "=", json.dumps(a[k], ensure_ascii=False)[:200])
    caps = a.get("capabilities", {})
    print("credits cap:", json.dumps(caps.get("credits", {}), ensure_ascii=False)[:300])
    print("dev_servers cap:", json.dumps(caps.get("dev_servers", {}), ensure_ascii=False))

# B try dev server on SITE_B
print()
s, b = req("POST", API + "/sites/%s/dev_servers" % SITE_B, tok=TOKEN_B, body={})
msg = json.dumps(b, ensure_ascii=False)[:400] if isinstance(b, (dict, list)) else repr(b)[:200]
print("B POST dev_servers ->", s, msg)

# A accounts credits too
s, b = req("GET", API + "/accounts?minimal=false", tok=C.TOKEN_A)
if isinstance(b, list) and b:
    a = b[0]
    caps = a.get("capabilities", {})
    print()
    print("A credits cap:", json.dumps(caps.get("credits", {}), ensure_ascii=False)[:300])
    for k in ("credits", "credit_balance"):
        if k in a:
            print("A", k, "=", json.dumps(a[k], ensure_ascii=False)[:200])
