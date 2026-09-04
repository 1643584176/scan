# -*- coding: utf-8 -*-
# _hk_matrix_fire.py - lock/unlock to fire hooks, poll matrix results
import sys, os, json, time, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_B

API = "https://api.netlify.com/api/v1"

def req(method, url, tok=None, body=None, timeout=30):
    r = urllib.request.Request(url, method=method)
    r.add_header("Authorization", "Bearer " + tok)
    data = json.dumps(body).encode() if body is not None else None
    if body is not None:
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, data=data, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as ex:
        return -1, str(ex)[:150]

ids = json.load(open(r"D:\scan\netlify_report\_hk_matrix_ids.json"))
print("matrix hooks:", len(ids))

# find a deploy to lock
s, deps = req("GET", API + "/sites/d2977de0-d24d-4544-81cb-933e610cad7d/deploys?per_page=1", tok=TOKEN_B)
DID = deps[0]["id"] if isinstance(deps, list) and deps else None
print("target deploy:", DID)

# fire: lock, wait, unlock
s, _ = req("POST", API + "/deploys/%s/lock" % DID, tok=TOKEN_B)
print("lock:", s)

for i in range(15):
    time.sleep(10)
    rows = []
    for k, hid in ids.items():
        s, h = req("GET", API + "/hooks/%s" % hid, tok=TOKEN_B)
        if isinstance(h, dict):
            rows.append("%s=%s%s" % (k, "OK" if h.get("success") is True else ("-" if h.get("success") is None else "F"),
                                     "d" if h.get("disabled") else ""))
        else:
            rows.append("%s=ERR" % k)
    print("poll %d: %s" % (i, " ".join(rows)), flush=True)
    # unlock once fired or after 3 polls
    if i == 3:
        s, _ = req("POST", API + "/deploys/%s/unlock" % DID, tok=TOKEN_B)
        print("unlock:", s, flush=True)
    # stop when all non-None
    allset = True
    for k, hid in ids.items():
        s, h = req("GET", API + "/hooks/%s" % hid, tok=TOKEN_B)
        if isinstance(h, dict) and h.get("success") is None:
            allset = False
    if allset:
        break
