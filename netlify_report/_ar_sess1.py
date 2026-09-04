# -*- coding: utf-8 -*-
# _ar_sess1.py - list sessions of agent runner, then delete it
import sys, os, json, urllib.request, urllib.error

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
                return resp.status, b[:800]
    except urllib.error.HTTPError as e:
        b = e.read(6000)
        try:
            return e.code, json.loads(b.decode("utf-8", "replace"))
        except Exception:
            return e.code, b[:500]
    except Exception as ex:
        return -1, str(ex)[:200]

s, d = req("GET", API + "/agent_runners/%s/sessions" % RID, tok=TOKEN_B)
print("sessions:", s, json.dumps(d, ensure_ascii=False)[:3000] if not isinstance(d, str) else d[:500])

# try delete/archive cleanup
s, d = req("DELETE", API + "/agent_runners/%s" % RID, tok=TOKEN_B)
if isinstance(d, bytes):
    d = d.decode("utf-8", "replace")
print("delete:", s, (json.dumps(d)[:200] if not isinstance(d, str) else d[:200]))
