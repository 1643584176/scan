# -*- coding: utf-8 -*-
# _hk_poll1.py - wait + poll hook states after lock/unlock
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

ids = json.load(open(r"D:\scan\netlify_report\_hk_ids2.txt"))
DID = "6a98cd570041c7459611eeae"

# unlock to fire deploy_unlocked
s, b = req("POST", API + "/deploys/%s/unlock" % DID, tok=TOKEN_B)
print("unlock:", s)

for i in range(12):
    time.sleep(10)
    out = []
    for name, hid in ids.items():
        s, h = req("GET", API + "/hooks/%s" % hid, tok=TOKEN_B)
        if isinstance(h, dict):
            out.append("%s: success=%r disabled=%r updated=%s" % (name, h.get("success"), h.get("disabled"), h.get("updated_at")))
        else:
            out.append("%s: %s" % (name, s))
    print("poll %d: %s" % (i, " | ".join(out)), flush=True)
    done = True
    for name, hid in ids.items():
        s, h = req("GET", API + "/hooks/%s" % hid, tok=TOKEN_B)
        if isinstance(h, dict) and h.get("success") is None:
            done = False
    if done:
        break
