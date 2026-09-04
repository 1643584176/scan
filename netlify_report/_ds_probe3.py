# -*- coding: utf-8 -*-
# _ds_probe3.py - validate SITE_B + dev_servers GET/POST on B
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_B

SITE_B = "d2977de0-d24d-4544-81cb-933e610cad7d"
API = "https://api.netlify.com/api/v1"

def req(method, url, tok=None, body=None, timeout=30):
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

print("== GET site B ==")
s, b = req("GET", API + "/sites/" + SITE_B, tok=TOKEN_B)
print(s, (b.get("name"), b.get("id"), b.get("account_slug")) if isinstance(b, dict) else repr(b)[:200])

print("== GET site B dev_servers ==")
s, b = req("GET", API + "/sites/%s/dev_servers" % SITE_B, tok=TOKEN_B)
print(s, json.dumps(b, ensure_ascii=False)[:400] if isinstance(b, (dict, list)) else repr(b)[:200])

print("== B accounts list (full ids) ==")
s, b = req("GET", API + "/accounts", tok=TOKEN_B)
if isinstance(b, list):
    for a in b:
        print({k: a.get(k) for k in ("id", "slug", "name", "type_id")})
else:
    print(s, repr(b)[:300])

print("== POST dev_servers (variants) ==")
bodies = [
    {},
    {"name": "probe-ds"},
    {"branch": "main", "repo_url": "https://github.com/libobo01/scan.git"},
    {"visual_editor_settings": {"enabled": True}},
]
for body in bodies:
    s, b = req("POST", API + "/sites/%s/dev_servers" % SITE_B, tok=TOKEN_B, body=body)
    msg = json.dumps(b, ensure_ascii=False)[:400] if isinstance(b, (dict, list)) else repr(b)[:200]
    print("  body=%s -> %s %s" % (json.dumps(body, ensure_ascii=False)[:120], s, msg))
