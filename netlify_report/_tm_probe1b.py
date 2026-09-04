# -*- coding: utf-8 -*-
# _tm_probe1b.py - team surface recon (focused)
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
            b = resp.read(30000)
            try:
                return resp.status, json.loads(b.decode("utf-8", "replace"))
            except Exception:
                return resp.status, b[:500]
    except urllib.error.HTTPError as e:
        b = e.read(2000)
        try:
            return e.code, json.loads(b.decode("utf-8", "replace"))
        except Exception:
            return e.code, b[:300]
    except Exception as ex:
        return -1, str(ex)[:200]

print("== B sees A team members? ==")
s, b = req("GET", API + "/%s/members" % TEAM_A, tok=TOKEN_B)
print(s, json.dumps(b, ensure_ascii=False)[:800] if isinstance(b, (dict, list)) else b)

print("== A sees B team members? ==")
s, b = req("GET", API + "/%s/members" % TEAM_B, tok=TOKEN_A)
print(s, json.dumps(b, ensure_ascii=False)[:800] if isinstance(b, (dict, list)) else b)

print("== A account collab caps ==")
s, b = req("GET", API + "/accounts?minimal=false", tok=TOKEN_A)
if isinstance(b, list) and b:
    acct = b[0]
    caps = acct.get("capabilities", {})
    print("slug:", acct.get("slug"), "| type:", acct.get("type"), "| roles_allowed:", acct.get("roles_allowed"))
    print("collab:", json.dumps(caps.get("collaborators", {}), ensure_ascii=False))
    print("sites:", json.dumps(caps.get("sites", {}), ensure_ascii=False))
    print("seats:", json.dumps(caps.get("seats", {}), ensure_ascii=False))
    # list all capability names (keys)
    print("cap keys:", sorted(caps.keys()))

print()
print("== A team members FULL (self) ==")
s, b = req("GET", API + "/%s/members" % TEAM_A, tok=TOKEN_A)
if isinstance(b, list):
    for m in b:
        print("-", m.get("email"), "| user_id:", m.get("user_id"), "| member id:", m.get("id"), "| role:", m.get("role"))
        c = m.get("capabilities", {})
        # count true/false
        trues = [k for k, v in c.items() if isinstance(v, dict) and v.get("r")]
        print("  cap count:", len(c), "readable:", len(trues))
        # print interesting caps
        for k in ("members", "billing", "shared_environment_variables", "sites", "builds", "env", "deploys", "audit", "account_usage", "reviews"):
            if k in c:
                print("   cap[%s]:" % k, json.dumps(c[k], ensure_ascii=False))
else:
    print(s, b)

print()
print("== B team members FULL (self) ==")
s, b = req("GET", API + "/%s/members" % TEAM_B, tok=TOKEN_B)
if isinstance(b, list):
    for m in b:
        print("-", m.get("email"), "| user_id:", m.get("user_id"), "| member id:", m.get("id"), "| role:", m.get("role"))
        c = m.get("capabilities", {})
        trues = [k for k, v in c.items() if isinstance(v, dict) and v.get("r")]
        print("  cap count:", len(c), "readable:", len(trues))
else:
    print(s, b)
