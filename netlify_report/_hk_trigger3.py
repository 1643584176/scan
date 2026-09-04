# -*- coding: utf-8 -*-
# _hk_trigger3.py - try deploy lock/unlock events + other event triggers for url hook
import sys, os, json, time, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_B

SITE_B = "d2977de0-d24d-4544-81cb-933e610cad7d"
API = "https://api.netlify.com/api/v1"

def req(method, url, tok=None, body=None, timeout=40):
    r = urllib.request.Request(url, method=method)
    if tok:
        r.add_header("Authorization", "Bearer " + tok)
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, data=data, timeout=timeout) as resp:
            b = resp.read(40000)
            try:
                return resp.status, json.loads(b.decode("utf-8", "replace"))
            except Exception:
                return resp.status, b[:800]
    except urllib.error.HTTPError as e:
        b = e.read(4000)
        try:
            return e.code, json.loads(b.decode("utf-8", "replace"))
        except Exception:
            return e.code, b[:400]
    except Exception as ex:
        return -1, str(ex)[:250]

new_ids = json.load(open(r"D:\scan\netlify_report\_hk_ids2.txt"))
print("hooks:", new_ids)

# get a published deploy id to lock
s, deps = req("GET", API + "/sites/%s/deploys?per_page=3" % SITE_B, tok=TOKEN_B)
did = None
if isinstance(deps, list) and deps:
    did = deps[0].get("id")
    print("latest deploy:", did, deps[0].get("state"), "locked:", deps[0].get("locked"))
else:
    print("no deploys:", s, repr(deps)[:200])

# try lock variants
lock_paths = [
    ("POST", "/sites/%s/deploys/%s/lock" % (SITE_B, did), None),
    ("PUT", "/sites/%s/deploys/%s/lock" % (SITE_B, did), None),
    ("PUT", "/deploys/%s" % did, {"locked": True}),
    ("PATCH", "/deploys/%s" % did, {"locked": True}),
    ("POST", "/deploys/%s/lock" % did, None),
]
for m, p, body in lock_paths:
    s, b = req(m, API + p, tok=TOKEN_B, body=body)
    msg = json.dumps(b, ensure_ascii=False)[:250] if isinstance(b, (dict, list)) else repr(b)[:200]
    print("%s %s -> %s %s" % (m, p, s, msg))
    # check hook state after each
    time.sleep(2)
    for name, hid in new_ids.items():
        s2, h = req("GET", API + "/hooks/%s" % hid, tok=TOKEN_B)
        if isinstance(h, dict):
            print("   hook %s: success=%r" % (name, h.get("success")))
