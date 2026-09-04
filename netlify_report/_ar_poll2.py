# -*- coding: utf-8 -*-
# _ar_poll2.py - poll run state after answering interaction
import sys, os, json, time, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_B

API = "https://api.netlify.com/api/v1"
RID = "6a98d6d818790895d7d5ac00"

def req(method, url, tok=None, timeout=30):
    r = urllib.request.Request(url, method=method)
    if tok:
        r.add_header("Authorization", "Bearer " + tok)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            b = resp.read(50000)
            try:
                return resp.status, json.loads(b.decode("utf-8", "replace"))
            except Exception:
                return resp.status, b[:500]
    except urllib.error.HTTPError as e:
        return e.code, e.read(2000)[:500]
    except Exception as ex:
        return -1, str(ex)[:200]

for i in range(30):
    time.sleep(8)
    s, d = req("GET", API + "/agent_runners/%s" % RID, tok=TOKEN_B)
    st = d.get("state") if isinstance(d, dict) else None
    ct = d.get("current_task") if isinstance(d, dict) else None
    print("poll %d: state=%s task=%s" % (i, st, str(ct)[:60]), flush=True)
    if st in ("done", "failed", "error", "stopped", "cancelled"):
        break
