# -*- coding: utf-8 -*-
# _ds_probe1.py - blackbox probe dev_servers create + subresource surface
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_A, TOKEN_B, SITE_A

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
            b = resp.read(20000)
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

B = API + "/sites/%s/dev_servers" % SITE_A

# 1. try POST create with empty and minimal bodies
bodies = [None, {}, {"name": "ds-probe"}, {"branch": "main"}, {"repo": {"branch": "main"}}]
for body in bodies:
    s, b = req("POST", B, tok=TOKEN_A, body=body)
    msg = json.dumps(b, ensure_ascii=False, indent=1)[:600] if isinstance(b, (dict, list)) else repr(b)[:300]
    print("POST body=%r -> %s\n%s" % (body, s, msg))
    print("---")
    if s == 201 or (isinstance(b, dict) and b.get("id")):
        print("CREATED id:", b.get("id") if isinstance(b, dict) else b)
        break

# 2. subresources
print("== subresource probe ==")
for p in ("", "/hooks", "/logs", "/status", "/config", "/activity"):
    s, b = req("GET", B + p, tok=TOKEN_A)
    msg = json.dumps(b, ensure_ascii=False)[:200] if isinstance(b, (dict, list)) else repr(b)[:150]
    print("GET .../dev_servers%s -> %s %s" % (p, s, msg))
