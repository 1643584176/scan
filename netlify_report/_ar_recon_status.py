# -*- coding: utf-8 -*-
# _ar_recon_status.py - inspect why agent stuck at await_input
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_B

API = "https://api.netlify.com/api/v1"
RID = json.load(open(r"D:\scan\netlify_report\_ar_recon_rid.json"))["rid"]

def req(method, url, tok=None, timeout=30):
    r = urllib.request.Request(url, method=method)
    if tok:
        r.add_header("Authorization", "Bearer " + tok)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            b = resp.read(150000)
            try:
                return resp.status, json.loads(b.decode("utf-8", "replace"))
            except Exception:
                return resp.status, b[:800]
    except urllib.error.HTTPError as e:
        b = e.read(6000)
        try:
            return e.code, json.loads(b.decode("utf-8", "replace"))
        except Exception:
            return e.code, b[:500]
    except Exception as ex:
        return -1, str(ex)[:200]

s, d = req("GET", API + "/agent_runners/%s" % RID, tok=TOKEN_B)
print("run:", s)
if isinstance(d, dict):
    for k in ("id", "state", "current_task", "steps_count", "total_steps", "created_at", "updated_at", "session_id", "dev_server_id"):
        print(" ", k, "=", d.get(k))
else:
    print(d)

s, d = req("GET", API + "/agent_runners/%s/sessions" % RID, tok=TOKEN_B)
print("\nsessions:", s)
if isinstance(d, dict):
    sess = d.get("sessions") or d.get("data") or ([d] if d.get("id") else None)
    if isinstance(sess, list):
        for s2 in sess:
            print("session:", s2.get("id"), "state:", s2.get("state"), "steps_count:", s2.get("steps_count"), "current_task:", s2.get("current_task"))
            res = s2.get("result") or {}
            if isinstance(res, dict):
                for k2 in ("state", "error", "final_report"):
                    if res.get(k2):
                        print("  result.%s:" % k2, json.dumps(res[k2], ensure_ascii=False)[:2000])
    else:
        print(json.dumps(d, ensure_ascii=False)[:4000])
else:
    print(d)
