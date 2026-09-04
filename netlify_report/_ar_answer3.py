# -*- coding: utf-8 -*-
# _ar_answer3.py - probe response array element format
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_B

API = "https://api.netlify.com/api/v1"
RID = "6a98d6d818790895d7d5ac00"
SID = "6a98d6d818790895d7d5ac02"
IID = "fe3ab820-8bae-44e9-8d7c-2f349427d727"

def req(method, url, tok=None, body=None, timeout=30):
    r = urllib.request.Request(url, method=method)
    if tok:
        r.add_header("Authorization", "Bearer " + tok)
    data = json.dumps(body).encode() if body is not None else None
    if body is not None:
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, data=data, timeout=timeout) as resp:
            b = resp.read(20000)
            try:
                return resp.status, json.loads(b.decode("utf-8", "replace"))
            except Exception:
                return resp.status, b[:400]
    except urllib.error.HTTPError as e:
        b = e.read(6000)
        try:
            return e.code, json.loads(b.decode("utf-8", "replace"))
        except Exception:
            return e.code, b[:300]
    except Exception as ex:
        return -1, str(ex)[:200]

# response array element guesses
for body in [
    {"refId": IID, "response": [{"option_index": 1}]},
    {"refId": IID, "response": [1]},
    {"refId": IID, "response": ["No, that recon was actually what I needed"]},
    {"refId": IID, "response": [{"answer": 1}]},
    {"refId": IID, "response": [{"selected_option": 1}]},
]:
    s, d = req("POST", API + "/agent_runners/%s/sessions/%s/answers" % (RID, SID), tok=TOKEN_B, body=body)
    print(json.dumps(body, ensure_ascii=False)[:120], "->", s, json.dumps(d, ensure_ascii=False)[:300] if not isinstance(d, str) else d)
