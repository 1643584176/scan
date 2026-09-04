# -*- coding: utf-8 -*-
# _identeer1.py - probe identeer-proxy endpoints (anon / A / B cookie)
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import COOKIE_A, COOKIE_B

BASE = "https://app.netlify.com/.netlify/functions"

def req(method, url, cookie=None, headers=None, body=None, timeout=25):
    r = urllib.request.Request(url, method=method)
    if cookie:
        r.add_header("Cookie", cookie)
    if headers:
        for k, v in headers.items():
            r.add_header(k, v)
    data = json.dumps(body).encode() if body is not None else None
    if body is not None:
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
            return e.code, b[:300]
    except Exception as ex:
        return -1, str(ex)[:200]

def show(tag, s, d):
    if isinstance(d, bytes):
        d = d.decode("utf-8", "replace")
    if isinstance(d, str):
        print("%-34s -> %s %s" % (tag, s, d[:400]))
    else:
        print("%-34s -> %s %s" % (tag, s, json.dumps(d, ensure_ascii=False)[:400]))

# 1) providers list
for tag, ck in (("anon", None), ("B", COOKIE_B), ("A", COOKIE_A)):
    s, d = req("GET", BASE + "/identeer-proxy/providers", cookie=ck)
    show("providers " + tag, s, d)
    if s == 200 and isinstance(d, list) and d and tag == "B":
        provs = d
        print("provider names:", [p.get("name") or p.get("slug") or p.get("id") for p in provs][:30])
        with open(r"D:\scan\netlify_report\_identeer_providers.json", "w") as f:
            json.dump(provs, f, ensure_ascii=False, indent=1)

# 2) connections endpoints with placeholder ids
for tag, ck in (("anon", None), ("B", COOKIE_B), ("A", COOKIE_A)):
    s, d = req("GET", BASE + "/identeer-proxy/connections/00000000-0000-0000-0000-000000000000", cookie=ck)
    show("connections uuid " + tag, s, d)
    s, d = req("GET", BASE + "/identeer-proxy/connections/dummy_slug", cookie=ck)
    show("connections slug " + tag, s, d)

# 3) auth url gen
for tag, ck in (("anon", None), ("B", COOKIE_B)):
    s, d = req("GET", BASE + "/identeer-proxy/auth/dummy_slug?redirect_uri=https://app.netlify.com/", cookie=ck)
    show("auth " + tag, s, d)
    s, d = req("GET", BASE + "/identeer-proxy/auth/00000000-0000-0000-0000-000000000000?redirect_uri=https://app.netlify.com/", cookie=ck)
    show("auth uuid " + tag, s, d)

# 4) disconnect
for tag, ck in (("anon", None), ("B", COOKIE_B)):
    s, d = req("POST", BASE + "/identeer-proxy/disconnect/dummy_slug", cookie=ck, body={})
    show("disconnect " + tag, s, d)

# 5) extensions-connections
for tag, ck in (("anon", None), ("B", COOKIE_B)):
    s, d = req("GET", BASE + "/extensions-connections", cookie=ck)
    show("extensions-connections " + tag, s, d)
