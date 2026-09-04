# -*- coding: utf-8 -*-
# _ar_recon2_out.py - fetch session result of network/env recon run
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_B

API = "https://api.netlify.com/api/v1"
RID = "6a98da92968b9a6f212f9775"

def req(method, url, tok=None, timeout=40):
    r = urllib.request.Request(url, method=method)
    if tok:
        r.add_header("Authorization", "Bearer " + tok)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            b = resp.read(200000)
            try:
                return resp.status, json.loads(b.decode("utf-8", "replace"))
            except Exception:
                return resp.status, b[:2000]
    except urllib.error.HTTPError as e:
        b = e.read(8000)
        try:
            return e.code, json.loads(b.decode("utf-8", "replace"))
        except Exception:
            return e.code, b[:800]
    except Exception as ex:
        return -1, str(ex)[:300]

s, d = req("GET", API + "/agent_runners/%s/sessions" % RID, tok=TOKEN_B)
print("sessions:", s)
if isinstance(d, list) and d:
    for sess in d:
        print("session:", sess.get("id"), "state:", sess.get("state"), "steps:", sess.get("steps_count"))
        print("usage:", json.dumps(sess.get("usage") or {}, ensure_ascii=False)[:300])
        res = sess.get("result") or {}
        if isinstance(res, dict):
            print("result keys:", list(res.keys()))
            for k in ("state", "final_report", "error", "summary"):
                if k in res and res[k]:
                    v = res[k]
                    txt = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
                    print("\n### result.%s:\n%s" % (k, txt[:6000]))
            for k2 in ("messages", "transcript", "steps", "events"):
                if k2 in res and res[k2]:
                    print("\n### result.%s (len %d):" % (k2, len(res[k2])))
                    print(json.dumps(res[k2], ensure_ascii=False)[:9000])
        else:
            print("result:", str(res)[:4000])
        it = sess.get("interactions")
        if it:
            print("\ninteractions:", json.dumps(it, ensure_ascii=False)[:2500])
else:
    print(json.dumps(d, ensure_ascii=False)[:3000])
