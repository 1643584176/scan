# -*- coding: utf-8 -*-
# _ar_probe2.py - watch created agent runner, dump detail fields
import sys, os, json, time, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_B

API = "https://api.netlify.com/api/v1"
RID = "6a98d5e6448c07a76d7babf3"

def req(method, url, tok=None, body=None, timeout=30):
    r = urllib.request.Request(url, method=method)
    if tok:
        r.add_header("Authorization", "Bearer " + tok)
    data = json.dumps(body).encode() if body is not None else None
    if body is not None:
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, data=data, timeout=timeout) as resp:
            b = resp.read(80000)
            try:
                return resp.status, json.loads(b.decode("utf-8", "replace"))
            except Exception:
                return resp.status, b[:1000]
    except urllib.error.HTTPError as e:
        b = e.read(8000)
        try:
            return e.code, json.loads(b.decode("utf-8", "replace"))
        except Exception:
            return e.code, b[:600]
    except Exception as ex:
        return -1, str(ex)[:200]

for i in range(10):
    time.sleep(6)
    s, d = req("GET", API + "/agent_runners/%s" % RID, tok=TOKEN_B)
    if isinstance(d, dict):
        keys = ["state", "title", "error", "result_summary", "usage", "logs", "command", "repo", "branch", "deploy_id"]
        print("poll %d: state=%s" % (i, d.get("state")), end="")
        for k in ("title", "error", "branch", "deploy_id"):
            if d.get(k):
                print(" %s=%r" % (k, str(d[k])[:80]), end="")
        print()
        # dump full once when terminal
        if d.get("state") in ("success", "failed", "error", "stopped", "cancelled"):
            print(json.dumps(d, ensure_ascii=False, indent=1)[:6000])
            break
    else:
        print("poll %d: %s %r" % (i, s, d)[:300])
        break
