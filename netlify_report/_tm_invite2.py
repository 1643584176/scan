# -*- coding: utf-8 -*-
# _tm_invite2.py - probe role validation on POST members + site-level sharing paths
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_A, TOKEN_B, TEAM_A, TEAM_B, SITE_A

API = "https://api.netlify.com/api/v1"

def req(method, url, tok=None, body=None, timeout=20):
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

# probe role values
for role in ("Owner", "Developer", "Billing Admin", "owner", "Administrator", "guest", "Member"):
    print("== POST A members role=%r ==" % role)
    body = {"email": "729488839@qq.com", "role": role}
    s, b = req("POST", API + "/%s/members" % TEAM_A, tok=TOKEN_A, body=body)
    if isinstance(b, (dict, list)):
        msg = b.get("message") or b.get("error") or json.dumps(b, ensure_ascii=False)[:200]
    else:
        msg = repr(b)[:200]
    print("  ", s, msg)

# maybe site-level share: check endpoints used by UI for adding people to site
print()
print("== probe site-level collaborator endpoints ==")
for path in ("/sites/%s/collaborators" % SITE_A,
             "/sites/%s/members" % SITE_A,
             "/%s/members" % TEAM_A + "?site_id=" + SITE_A,
             "/accounts/%s/members" % TEAM_A):
    s, b = req("GET", API + path, tok=TOKEN_A)
    msg = json.dumps(b, ensure_ascii=False)[:200] if isinstance(b, (dict, list)) else repr(b)[:200]
    print("GET", path, "->", s, msg)
