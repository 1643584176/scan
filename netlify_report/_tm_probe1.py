# -*- coding: utf-8 -*-
# _tm_probe1.py - team/member surface recon (read-only)
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_A, TOKEN_B, TEAM_A, TEAM_B

API = "https://api.netlify.com/api/v1"

def req(method, url, tok=None, body=None, timeout=15):
    r = urllib.request.Request(url, method=method)
    if tok:
        r.add_header("Authorization", "Bearer " + tok)
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, data=data, timeout=timeout) as resp:
            b = resp.read(4000)
            try:
                return resp.status, json.loads(b.decode("utf-8", "replace"))
            except Exception:
                return resp.status, b[:500]
    except urllib.error.HTTPError as e:
        b = e.read(1000)
        try:
            return e.code, json.loads(b.decode("utf-8", "replace"))
        except Exception:
            return e.code, b[:300]
    except Exception as ex:
        return -1, str(ex)[:200]

print("== A accounts (minimal) ==")
s, b = req("GET", API + "/accounts?minimal=false", tok=TOKEN_A)
print(s, json.dumps(b, ensure_ascii=False, indent=1)[:3000] if isinstance(b, dict) else b)

print()
print("== B accounts (minimal) ==")
s, b = req("GET", API + "/accounts?minimal=false", tok=TOKEN_B)
print(s, json.dumps(b, ensure_ascii=False, indent=1)[:3000] if isinstance(b, dict) else b)

print()
print("== A team members ==")
s, b = req("GET", API + "/%s/members" % TEAM_A, tok=TOKEN_A)
print(s, json.dumps(b, ensure_ascii=False, indent=1)[:2000] if isinstance(b, (dict, list)) else b)

print()
print("== B team members ==")
s, b = req("GET", API + "/%s/members" % TEAM_B, tok=TOKEN_B)
print(s, json.dumps(b, ensure_ascii=False, indent=1)[:2000] if isinstance(b, (dict, list)) else b)

print()
print("== B sees A team members? ==")
s, b = req("GET", API + "/%s/members" % TEAM_A, tok=TOKEN_B)
print(s, json.dumps(b, ensure_ascii=False)[:500] if isinstance(b, (dict, list)) else b)

print()
print("== A sees B team members? ==")
s, b = req("GET", API + "/%s/members" % TEAM_B, tok=TOKEN_A)
print(s, json.dumps(b, ensure_ascii=False)[:500] if isinstance(b, (dict, list)) else b)
