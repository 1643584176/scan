# -*- coding: utf-8 -*-
# _tm_sitemembers.py - probe site-level members API surface
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_A, TOKEN_B, TEAM_A, TEAM_B, SITE_A

API = "https://api.netlify.com/api/v1"

def req(method, url, tok=None, body=None, timeout=20):
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
                return resp.status, b
    except urllib.error.HTTPError as e:
        b = e.read(3000)
        try:
            return e.code, json.loads(b.decode("utf-8", "replace"))
        except Exception:
            return e.code, b
    except Exception as ex:
        return -1, str(ex)

BASE = API + "/sites/%s/members" % SITE_A

print("== GET site members full ==")
s, b = req("GET", BASE, tok=TOKEN_A)
print(s, json.dumps(b, ensure_ascii=False, indent=1)[:2500] if isinstance(b, (dict, list)) else repr(b)[:400])

print()
print("== POST site members variants ==")
bodies = [
    {"email": "729488839@qq.com", "role": "Developer"},
    {"email": "729488839@qq.com", "role": "Owner"},
    {"email": "729488839@qq.com", "role": "Reviewer"},
    {"email": "729488839@qq.com"},
    {"email": "729488839@qq.com", "role": "Developer", "site_access": "all"},
]
for body in bodies:
    s, b = req("POST", BASE, tok=TOKEN_A, body=body)
    msg = json.dumps(b, ensure_ascii=False)[:300] if isinstance(b, (dict, list)) else repr(b)[:200]
    print("  body=%s -> %s %s" % (json.dumps(body, ensure_ascii=False)[:100], s, msg))
