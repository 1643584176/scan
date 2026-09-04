# -*- coding: utf-8 -*-
# _ar_answer1.py - try answering agent interaction (probe payload schema)
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_B, TOKEN_A

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

# probe 1: empty body - what does server require?
s, d = req("POST", API + "/agent_runners/%s/sessions/%s/answers" % (RID, SID), tok=TOKEN_B, body={})
print("empty {}:", s, json.dumps(d, ensure_ascii=False)[:400] if not isinstance(d, str) else d)

# probe 2: only interaction_id
s, d = req("POST", API + "/agent_runners/%s/sessions/%s/answers" % (RID, SID), tok=TOKEN_B, body={"interaction_id": IID})
print("iid only:", s, json.dumps(d, ensure_ascii=False)[:400] if not isinstance(d, str) else d)

# probe 3: cross-account answer with A token (IDOR check)
s, d = req("POST", API + "/agent_runners/%s/sessions/%s/answers" % (RID, SID), tok=TOKEN_A, body={"interaction_id": IID})
print("cross-account A->B:", s, json.dumps(d, ensure_ascii=False)[:400] if not isinstance(d, str) else d)

# probe 4: nonexistent interaction id (self)
s, d = req("POST", API + "/agent_runners/%s/sessions/%s/answers" % (RID, SID), tok=TOKEN_B, body={"interaction_id": "00000000-0000-0000-0000-000000000000"})
print("bad iid:", s, json.dumps(d, ensure_ascii=False)[:400] if not isinstance(d, str) else d)
