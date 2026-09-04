# -*- coding: utf-8 -*-
# _tm_invite.py - (1) recon B->A cross read; (2) invite B into A team as Reviewer
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_A, TOKEN_B, TEAM_A, TEAM_B

API = "https://api.netlify.com/api/v1"

def req(method, url, tok=None, body=None, raw=False, timeout=20):
    r = urllib.request.Request(url, method=method)
    if tok:
        r.add_header("Authorization", "Bearer " + tok)
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, data=data, timeout=timeout) as resp:
            b = resp.read(30000)
            try:
                return resp.status, json.loads(b.decode("utf-8", "replace"))
            except Exception:
                return resp.status, b
    except urllib.error.HTTPError as e:
        b = e.read(3000)
        try:
            return e.code, json.loads(b.decode("utf-8", "replace"))
        except Exception:
            return e.code, b
    except Exception as ex:
        return -1, str(ex)

# 1. B -> A members (rerun for clarity, dump raw)
print("== B->A /members ==")
s, b = req("GET", API + "/%s/members" % TEAM_A, tok=TOKEN_B, raw=True)
print("status:", s)
print("body:", repr(b)[:500])

# 2. Invite B (Reviewer) into A team
print()
print("== POST A members (invite B as Reviewer) ==")
body = {"email": "729488839@qq.com", "role": "Reviewer"}
s, b = req("POST", API + "/%s/members" % TEAM_A, tok=TOKEN_A, body=body)
print("status:", s)
print("body:", json.dumps(b, ensure_ascii=False, indent=1)[:1500] if isinstance(b, (dict, list)) else repr(b)[:500])
