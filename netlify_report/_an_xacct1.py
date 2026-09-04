# -*- coding: utf-8 -*-
# _an_xacct1.py - analytics-api v2 cross-account checks
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import COOKIE_A, COOKIE_B

BASE = "https://app.netlify.com/access-control/analytics-api/v2"
ACC_B = "6a97b6454fef0db964f75db6"
ACC_A = "6a979dd2ae93f47d55b62897"

def req(method, url, cookie=None, timeout=30):
    r = urllib.request.Request(url, method=method)
    if cookie:
        r.add_header("Cookie", cookie)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            b = resp.read(60000)
            try:
                return resp.status, json.loads(b.decode("utf-8", "replace"))
            except Exception:
                return resp.status, b[:800]
    except urllib.error.HTTPError as e:
        b = e.read(8000)
        try:
            return e.code, json.loads(b.decode("utf-8", "replace"))
        except Exception:
            return e.code, b[:600]
    except Exception as ex:
        return -1, str(ex)[:250]

def show(tag, s, d):
    if isinstance(d, bytes):
        d = d.decode("utf-8", "replace")
    if isinstance(d, str):
        print("%-46s -> %s %s" % (tag, s, d[:350]))
    else:
        print("%-46s -> %s %s" % (tag, s, json.dumps(d, ensure_ascii=False)[:350]))

F = "2026-08-01"
T = "2026-09-02"

tests = [
    # account usage_insights: B own vs A cross
    ("B own acct builds", COOKIE_B, "/accounts/%s/usage_insights/builds?from=%s&to=%s&resolution=day" % (ACC_B, F, T)),
    ("B->A acct builds", COOKIE_B, "/accounts/%s/usage_insights/builds?from=%s&to=%s&resolution=day" % (ACC_A, F, T)),
    ("A own acct builds", COOKIE_A, "/accounts/%s/usage_insights/builds?from=%s&to=%s&resolution=day" % (ACC_A, F, T)),
    ("A->B acct builds", COOKIE_A, "/accounts/%s/usage_insights/builds?from=%s&to=%s&resolution=day" % (ACC_B, F, T)),
    # site pageviews: B own vs A site
    ("B own site pv", COOKIE_B, "/sec-b-08v4pk.netlify.app/pageviews?from=%s&to=%s&timezone=UTC&resolution=day" % (F, T)),
    ("B->A site pv", COOKIE_B, "/sec-test-rcf6lz.netlify.app/pageviews?from=%s&to=%s&timezone=UTC&resolution=day" % (F, T)),
    ("A own site pv", COOKIE_A, "/sec-test-rcf6lz.netlify.app/pageviews?from=%s&to=%s&timezone=UTC&resolution=day" % (F, T)),
    ("A->B site pv", COOKIE_A, "/sec-b-08v4pk.netlify.app/pageviews?from=%s&to=%s&timezone=UTC&resolution=day" % (F, T)),
    ("anon acct builds", None, "/accounts/%s/usage_insights/builds?from=%s&to=%s&resolution=day" % (ACC_B, F, T)),
    ("anon site pv", None, "/sec-b-08v4pk.netlify.app/pageviews?from=%s&to=%s&timezone=UTC&resolution=day" % (F, T)),
    # rum endpoint on other site
    ("B->A rum", COOKIE_B, "/sec-test-rcf6lz.netlify.app/rum/country?from=%s&to=%s&timezone=UTC&resolution=day" % (F, T)),
    # ranking not found
    ("B->A notfound", COOKIE_B, "/sec-test-rcf6lz.netlify.app/ranking/not_found?from=%s&to=%s&timezone=UTC&limit=15" % (F, T)),
]
for tag, ck, p in tests:
    s, d = req("GET", BASE + p, cookie=ck)
    show(tag, s, d)
