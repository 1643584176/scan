# -*- coding: utf-8 -*-
# _ext_probe1.py - cookie validity + extension write functions (cross-account)
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import COOKIE_A, COOKIE_B, USER_A, USER_B, TEAM_A, SITE_A

APP = "https://app.netlify.com"

def req(method, url, cookie=None, body=None, timeout=25):
    r = urllib.request.Request(url, method=method)
    if cookie:
        r.add_header("Cookie", cookie)
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

# 1. cookie validity check via database-query (known cookie-authed internal fn)
print("== cookie check: database-query check ==")
s, b = req("POST", APP + "/.netlify/functions/database-query",
           cookie=COOKIE_A, body={"siteId": SITE_A, "action": "check"})
print("A:", s, json.dumps(b, ensure_ascii=False)[:300] if isinstance(b, (dict, list)) else repr(b)[:200])

# 2. probe extension write functions shape (read-only first: what args do they need?)
print()
print("== extension fn probing (A cookie, own account) ==")
probes = [
    ("POST", "/.netlify/functions/fetch-site-configuration", {"siteId": SITE_A}),
    ("POST", "/.netlify/functions/fetch-installed-extensions-for-team", {"accountId": TEAM_A}),
    ("POST", "/.netlify/functions/fetch-installed-extensions-for-team", {"accountSlug": TEAM_A}),
    ("POST", "/.netlify/functions/fetch-relevant-installed-extensions-for-site", {"siteId": SITE_A}),
    ("GET", "/.netlify/functions/fetch-extensions", None),
    ("POST", "/.netlify/functions/fetch-extensions", {}),
]
for m, p, body in probes:
    s, b = req(m, APP + p, cookie=COOKIE_A, body=body)
    msg = json.dumps(b, ensure_ascii=False)[:250] if isinstance(b, (dict, list)) else repr(b)[:200]
    print("%s %s body=%s -> %s %s" % (m, p, json.dumps(body)[:80] if body else None, s, msg))
