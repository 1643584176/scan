# -*- coding: utf-8 -*-
# _ar_recon3_out.py - fetch session result of token identity run
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_B

API = "https://api.netlify.com/api/v1"
RID = "6a98db3f0041c71a1811ee8d"

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
        res = sess.get("result") or {}
        if isinstance(res, dict):
            for k in ("state", "final_report", "error", "summary"):
                if k in res and res[k]:
                    v = res[k]
                    print("\n### result.%s:" % k)
                    print(v if isinstance(v, str) else json.dumps(v, ensure_ascii=False))
        it = sess.get("interactions")
        if it:
            print("\ninteractions:", json.dumps(it, ensure_ascii=False)[:2500])
else:
    print(json.dumps(d, ensure_ascii=False)[:3000])
