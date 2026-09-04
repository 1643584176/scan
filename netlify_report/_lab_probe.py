# -*- coding: utf-8 -*-
# _lab_probe.py - labs-list/toggle probe + bitbucket-self-hosted context finder
import sys, os, json, re, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import COOKIE_A, COOKIE_B

FN = "https://app.netlify.com/.netlify/functions"

def req(method, url, cookie=None, body=None, timeout=25):
    r = urllib.request.Request(url, method=method)
    if cookie:
        r.add_header("Cookie", cookie)
    data = json.dumps(body).encode() if body is not None else None
    if body is not None:
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, data=data, timeout=timeout) as resp:
            b = resp.read(60000)
            try:
                return resp.status, json.loads(b.decode("utf-8", "replace"))
            except Exception:
                return resp.status, b[:800]
    except urllib.error.HTTPError as e:
        b = e.read(6000)
        try:
            return e.code, json.loads(b.decode("utf-8", "replace"))
        except Exception:
            return e.code, b[:500]
    except Exception as ex:
        return -1, str(ex)[:200]

# labs-list
for tag, ck in (("anon", None), ("A", COOKIE_A), ("B", COOKIE_B)):
    s, d = req("GET", FN + "/labs-list", cookie=ck)
    if isinstance(d, list):
        print("labs-list %s: %d features" % (tag, len(d)))
        for f in d[:30]:
            print("   ", json.dumps(f, ensure_ascii=False)[:220])
    else:
        print("labs-list %s -> %s %r" % (tag, s, d)[:300])
