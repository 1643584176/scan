# -*- coding: utf-8 -*-
# _edgeacc1.py - fetch edge access token for dev server, then try access
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_B

API = "https://api.netlify.com"
SITE_B = "d2977de0-d24d-4544-81cb-933e610cad7d"
DS_HOST = "devserver-ar-6a98d6d818790895d7d5ac00--sec-b-08v4pk.netlify.app"
DS_URL = "https://" + DS_HOST

def jreq(method, url, tok=None, body=None, timeout=25, headers=None):
    r = urllib.request.Request(url, method=method)
    if tok:
        r.add_header("Authorization", "Bearer " + tok)
    for k, v in (headers or {}).items():
        r.add_header(k, v)
    data = json.dumps(body).encode() if body is not None else None
    if body is not None:
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, data=data, timeout=timeout) as resp:
            b = resp.read(30000)
            return resp.status, dict(resp.headers), b
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read(30000)
    except Exception as ex:
        return -1, {}, str(ex)[:300].encode()

# 1. fetch edge access token
s, h, b = jreq("POST", API + "/auth/edge-access", tok=TOKEN_B,
               body={"site_id": SITE_B, "domain": DS_HOST})
print("edge-access:", s, h.get("Content-Type"))
try:
    d = json.loads(b.decode("utf-8", "replace"))
    print(json.dumps(d, ensure_ascii=False)[:800])
    tok = (d.get("data") or {}).get("edge_access") or d.get("edge_access")
except Exception:
    print(b[:500])
    tok = None

if not tok:
    print("no token")
    sys.exit()

print("\ntoken len:", len(tok), tok[:40], "...")
json.dump({"tok": tok}, open(r"D:\scan\netlify_report\_edge_tok.json", "w"))

# 2. try access dev server with token in various auth positions
for name, hdrs in [
    ("cookie nf_edge_access", {"Cookie": "nf_edge_access=%s" % tok}),
    ("cookie edge_access", {"Cookie": "edge_access=%s" % tok}),
    ("header X-Edge-Access", {"X-Edge-Access": tok}),
    ("header X-Edge-Access-Token", {"X-Edge-Access-Token": tok}),
    ("auth bearer", {"Authorization": "Bearer %s" % tok}),
    ("query token", None),
]:
    if name == "query token":
        url = DS_URL + "/?edge_access=" + tok
    else:
        url = DS_URL + "/"
    s2, h2, b2 = jreq("GET", url, headers=hdrs)
    ct = h2.get("Content-Type", "")
    bodytxt = b2.decode("utf-8", "replace")[:200].replace("\n", " ")
    print("%-22s -> %s ct=%s %s" % (name, s2, ct, bodytxt))
    if s2 == 200:
        print("!!! GOT 200 with", name)
        break

# 3. callback path directly
s2, h2, b2 = jreq("GET", DS_URL + "/.netlify/callback", headers={"Cookie": "nf_edge_access=%s" % tok})
print("callback:", s2, h2.get("Content-Type"), b2.decode("utf-8", "replace")[:300].replace("\n", " "))
