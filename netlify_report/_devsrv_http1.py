# -*- coding: utf-8 -*-
# _devsrv_http1.py - probe public dev server URL (anon + auth) and lookup with dev domain
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_B

API = "https://api.netlify.com/api/v1"
DS_URL = "https://devserver-ar-6a98d6d818790895d7d5ac00--sec-b-08v4pk.netlify.app"

def req(method, url, tok=None, timeout=25, headers=None):
    r = urllib.request.Request(url, method=method)
    if tok:
        r.add_header("Authorization", "Bearer " + tok)
    for k, v in (headers or {}).items():
        r.add_header(k, v)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            b = resp.read(6000)
            return resp.status, dict(resp.headers), b[:3000]
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read(3000)[:1500]
    except Exception as ex:
        return -1, {}, str(ex)[:200]

# 1. anon GET root of dev server
s, h, b = req("GET", DS_URL + "/")
print("anon root:", s)
print("  server:", h.get("Server"), "| ct:", h.get("Content-Type"))
print("  body:", b.decode("utf-8", "replace")[:400].replace("\n", " ") if isinstance(b, bytes) else b)

# 2. anon common paths
for p in ("/.netlify/functions/", "/.netlify/dev-server/", "/__netlify/", "/.netlify/status", "/health", "/.netlify/dev-server-status"):
    s2, h2, b2 = req("GET", DS_URL + p)
    print("anon %-28s -> %s ct=%s body=%s" % (p, s2, h2.get("Content-Type", ""),
          (b2.decode("utf-8", "replace")[:120] if isinstance(b2, bytes) else str(b2)[:120]).replace("\n", " ")))

# 3. with B token
s, h, b = req("GET", DS_URL + "/", tok=TOKEN_B)
print("auth root:", s, (b.decode("utf-8", "replace")[:200] if isinstance(b, bytes) else b))

# 4. lookup with dev server domain (B token)
def jreq(method, url, tok=None, timeout=25):
    r = urllib.request.Request(url, method=method)
    if tok:
        r.add_header("Authorization", "Bearer " + tok)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read(20000).decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        b = e.read(4000)
        try:
            return e.code, json.loads(b.decode("utf-8", "replace"))
        except Exception:
            return e.code, b[:300]
    except Exception as ex:
        return -1, str(ex)[:200]

s, d = jreq("POST", API + "/dev_servers/lookup?domain=%s" % "devserver-ar-6a98d6d818790895d7d5ac00--sec-b-08v4pk.netlify.app", tok=TOKEN_B)
print("lookup dev-domain:", s, json.dumps(d, ensure_ascii=False)[:600] if not isinstance(d, str) else d)
s, d = jreq("POST", API + "/dev_servers/lookup?domain=%s" % "devserver-ar-6a98d6d818790895d7d5ac00--sec-b-08v4pk", tok=TOKEN_B)
print("lookup dev-name:", s, json.dumps(d, ensure_ascii=False)[:600] if not isinstance(d, str) else d)
