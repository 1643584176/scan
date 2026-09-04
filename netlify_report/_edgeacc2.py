# -*- coding: utf-8 -*-
# _edgeacc2.py - edge-access token authz matrix + health anon
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_A, TOKEN_B

API = "https://api.netlify.com"
SITE_A = "04f08ff6-f274-47ac-b6d7-5fb1e055f3b4"
SITE_B = "d2977de0-d24d-4544-81cb-933e610cad7d"
DS_HOST = "devserver-ar-6a98d6d818790895d7d5ac00--sec-b-08v4pk.netlify.app"

def jreq(method, url, tok=None, body=None, timeout=20):
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
                return resp.status, b[:300]
    except urllib.error.HTTPError as e:
        b = e.read(4000)
        try:
            return e.code, json.loads(b.decode("utf-8", "replace"))
        except Exception:
            return e.code, b[:300]
    except Exception as ex:
        return -1, str(ex)[:200]

def show(tag, s, d, cut=400):
    out = json.dumps(d, ensure_ascii=False) if not isinstance(d, str) else d
    print("%-58s -> %s %s" % (tag, s, out[:cut]))

# 1. anon /health on dev server
def raw(url, headers=None):
    r = urllib.request.Request(url)
    for k, v in (headers or {}).items():
        r.add_header(k, v)
    try:
        with urllib.request.urlopen(r, timeout=15) as resp:
            return resp.status, resp.read(1000)[:300]
    except urllib.error.HTTPError as e:
        return e.code, e.read(2000)[:400]
    except Exception as ex:
        return -1, str(ex)[:200]

s, b = raw("https://" + DS_HOST + "/health")
print("anon devserver /health:", s, b)

# 2. cross-account: A token, site_id=SITE_B
show("A token site=B", *jreq("POST", API + "/auth/edge-access", tok=TOKEN_A,
     body={"site_id": SITE_B, "domain": DS_HOST}))
# 3. own site + own domain (B) baseline
show("B token site=B dom=B", *jreq("POST", API + "/auth/edge-access", tok=TOKEN_B,
     body={"site_id": SITE_B, "domain": DS_HOST}))
# 4. own site + arbitrary external domain
show("B token site=B dom=evil.com", *jreq("POST", API + "/auth/edge-access", tok=TOKEN_B,
     body={"site_id": SITE_B, "domain": "evil.com"}))
# 5. own site + A's production domain
show("B token site=B dom=A-prod", *jreq("POST", API + "/auth/edge-access", tok=TOKEN_B,
     body={"site_id": SITE_B, "domain": "sec-a.netlify.app"}))
# 6. other site's domain on B token (guess another tenant? use random netlify.app name)
show("B token site=B dom=rand.netlify.app", *jreq("POST", API + "/auth/edge-access", tok=TOKEN_B,
     body={"site_id": SITE_B, "domain": "someoneelse-12345.netlify.app"}))
# 7. nonexistent site
show("B token site=deadbeef", *jreq("POST", API + "/auth/edge-access", tok=TOKEN_B,
     body={"site_id": "deadbeef-dead-dead-dead-deaddeaddead", "domain": DS_HOST}))
# 8. no domain
show("B token site=B no domain", *jreq("POST", API + "/auth/edge-access", tok=TOKEN_B,
     body={"site_id": SITE_B}))
# 9. anon
show("anon site=B", *jreq("POST", API + "/auth/edge-access",
     body={"site_id": SITE_B, "domain": DS_HOST}))
