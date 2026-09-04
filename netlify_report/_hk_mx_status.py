# -*- coding: utf-8 -*-
# _hk_mx_status.py - dump final state of matrix hooks
import sys, os, json, urllib.request, urllib.error

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
        b = e.read(2000)
        try:
            return e.code, json.loads(b.decode("utf-8", "replace"))
        except Exception:
            return e.code, b[:200]
    except Exception as ex:
        return -1, str(ex)[:150]

ids = json.load(open(r"D:\scan\netlify_report\_hk_matrix_ids.json"))
for k, hid in ids.items():
    s, h = req("GET", API + "/hooks/%s" % hid, tok=TOKEN_B)
    if isinstance(h, dict):
        print("%s: event=%s success=%r disabled=%r updated=%s" % (
            k, h.get("event"), h.get("success"), h.get("disabled"), (h.get("updated_at") or "")[:19]))
    else:
        print("%s: GET %s %r" % (k, s, h))
