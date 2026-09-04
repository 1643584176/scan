# -*- coding: utf-8 -*-
# _ext_probe2.py - extension fns with teamId/accountId variants (query+body)
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import COOKIE_A, TEAM_A, SITE_A, TOKEN_A

APP = "https://app.netlify.com"
API = "https://api.netlify.com/api/v1"

def req(method, url, cookie=None, body=None, tok=None, timeout=25):
    r = urllib.request.Request(url, method=method)
    if cookie:
        r.add_header("Cookie", cookie)
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
        b = e.read(4000)
        try:
            return e.code, json.loads(b.decode("utf-8", "replace"))
        except Exception:
            return e.code, b[:400]
    except Exception as ex:
        return -1, str(ex)[:200]

# get account id
s, b = req("GET", API + "/accounts", tok=TOKEN_A)
acc_id = None
if isinstance(b, list) and b:
    acc_id = b[0].get("id")
    print("account id:", acc_id, "| slug:", b[0].get("slug"))
acc_ids = [acc_id, TEAM_A] if acc_id else [TEAM_A]

# fetch-extensions: teamId as query param
print()
for key in ("teamId", "accountId", "team_id", "account_id", "accountSlug"):
    for val in (TEAM_A, acc_id):
        if not val:
            continue
        s, b = req("POST", APP + "/.netlify/functions/fetch-extensions?%s=%s" % (key, val), cookie=COOKIE_A, body={})
        msg = json.dumps(b, ensure_ascii=False)[:250] if isinstance(b, (dict, list)) else repr(b)[:200]
        print("fetch-extensions ?%s=%s -> %s %s" % (key, val, s, msg))

# fetch-site-configuration via query
print()
for key in ("siteId", "site_id", "id"):
    s, b = req("POST", APP + "/.netlify/functions/fetch-site-configuration?%s=%s" % (key, SITE_A), cookie=COOKIE_A, body={})
    msg = json.dumps(b, ensure_ascii=False)[:250] if isinstance(b, (dict, list)) else repr(b)[:200]
    print("fetch-site-configuration ?%s= -> %s %s" % (key, s, msg))

# fetch-relevant-installed-extensions-for-site with teamId query
print()
s, b = req("POST", APP + "/.netlify/functions/fetch-relevant-installed-extensions-for-site?siteId=%s&teamId=%s" % (SITE_A, TEAM_A), cookie=COOKIE_A, body={})
msg = json.dumps(b, ensure_ascii=False)[:400] if isinstance(b, (dict, list)) else repr(b)[:200]
print("fetch-relevant-installed-extensions-for-site (siteId+teamId) -> %s %s" % (s, msg))

# fetch-installed-extensions-for-team with teamId query
print()
for val in (TEAM_A, acc_id):
    if not val:
        continue
    s, b = req("POST", APP + "/.netlify/functions/fetch-installed-extensions-for-team?teamId=%s" % val, cookie=COOKIE_A, body={})
    msg = json.dumps(b, ensure_ascii=False)[:400] if isinstance(b, (dict, list)) else repr(b)[:200]
    print("fetch-installed-extensions-for-team ?teamId=%s -> %s %s" % (val, s, msg))
