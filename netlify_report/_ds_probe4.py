# -*- coding: utf-8 -*-
# _ds_probe4.py - fresh site on B + POST dev_servers; path variants
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_B, TOKEN_A
import _net_creds as C

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

# 1. fresh site on B
print("== B create fresh site ==")
s, b = req("POST", API + "/sites", tok=TOKEN_B, body={})
print(s, (b.get("id"), b.get("name"), b.get("account_slug")) if isinstance(b, dict) else repr(b)[:300])
if not (isinstance(b, dict) and b.get("id")):
    print("cannot create site:", s, repr(b)[:300])
    sys.exit(0)
NS = b["id"]
print("new site:", NS)

# 2. POST dev_servers on fresh site
print()
print("== POST dev_servers on fresh site ==")
for body in ({}, {"name": "ds1"}, {"branch": "main"}):
    s, b = req("POST", API + "/sites/%s/dev_servers" % NS, tok=TOKEN_B, body=body)
    msg = json.dumps(b, ensure_ascii=False)[:400] if isinstance(b, (dict, list)) else repr(b)[:200]
    print("  %s -> %s %s" % (json.dumps(body)[:80], s, msg))

# 3. path variants on A (known 403 route) & B
print()
print("== path variants ==")
for p in ("/sites/%s/dev-servers" % NS,
          "/sites/%s/devserver" % NS,
          "/sites/%s/dev_servers/" % NS,
          "/accounts/libobo01/dev_servers"):
    s, b = req("POST", API + p, tok=TOKEN_B, body={})
    msg = json.dumps(b, ensure_ascii=False)[:200] if isinstance(b, (dict, list)) else repr(b)[:150]
    print("  POST %s -> %s %s" % (p, s, msg))

# 4. A-site POST with A body including repo (A had 403; check whether message changes with params)
print()
print("== A variants ==")
SITE_A = C.SITE_A
for p, body in (("/sites/%s/dev_servers" % SITE_A, {"repo": {"provider": "github"}}),
                ("/sites/%s/dev_servers" % SITE_A, {"live": True}),
                ("/sites/%s/dev_servers" % SITE_A, {"state": "running"})):
    s, b = req("POST", API + p, tok=C.TOKEN_A, body=body)
    msg = json.dumps(b, ensure_ascii=False)[:300] if isinstance(b, (dict, list)) else repr(b)[:200]
    print("  POST %s body=%s -> %s %s" % (p, json.dumps(body)[:60], s, msg))

# cleanup fresh site
print()
print("== cleanup ==")
s, b = req("DELETE", API + "/sites/" + NS, tok=TOKEN_B)
print("DELETE site:", s, repr(b)[:200])
