# -*- coding: utf-8 -*-
# _newpaths1.py - probe swagger-external paths found in net_lib.js client
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_A, TOKEN_B

API = "https://api.netlify.com/api/v1"
ACC_B = "6a97b6454fef0db964f75db6"   # B account uuid
ACC_A = "6a979dd2ae93f47d55b62897"   # A account uuid
SITE_B = "d2977de0-d24d-4544-81cb-933e610cad7d"
SITE_A = "04f08ff6-f274-47ac-b6d7-5fb1e055f3b4"

def req(method, url, tok=None, body=None, timeout=25):
    r = urllib.request.Request(url, method=method)
    if tok:
        r.add_header("Authorization", "Bearer " + tok)
    data = json.dumps(body).encode() if body is not None else None
    if body is not None:
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, data=data, timeout=timeout) as resp:
            b = resp.read(40000)
            try:
                return resp.status, json.loads(b.decode("utf-8", "replace"))
            except Exception:
                return resp.status, b[:400]
    except urllib.error.HTTPError as e:
        b = e.read(4000)
        try:
            return e.code, json.loads(b.decode("utf-8", "replace"))
        except Exception:
            return e.code, b[:300]
    except Exception as ex:
        return -1, str(ex)[:150]

def show(tag, s, d):
    if isinstance(d, bytes):
        d = d.decode("utf-8", "replace")
    if isinstance(d, str):
        print("%-42s -> %s %s" % (tag, s, d[:260]))
    else:
        print("%-42s -> %s %s" % (tag, s, json.dumps(d, ensure_ascii=False)[:260]))

T = TOKEN_B
paths = [
    ("GET", "/organizations", None),
    ("GET", "/organizations/%s" % ACC_B, None),
    ("GET", "/accounts/%s/organizations" % ACC_B, None),
    ("GET", "/blobs/%s" % SITE_B, None),
    ("GET", "/blobs/%s" % SITE_A, None),
    ("GET", "/accounts/%s/sites_summary" % ACC_B, None),
    ("GET", "/accounts/%s/sites_summary" % ACC_A, None),
    ("GET", "/%s/billing/credit_usage" % ACC_B, None),
    ("GET", "/accounts/%s/compliance" % ACC_B, None),
    ("GET", "/dev_servers/lookup?domain=sec-b-08v4pk.netlify.app", None),
    ("GET", "/dev_servers/lookup?domain=sec-test-rcf6lz.netlify.app", None),
    ("GET", "/drop", None),
    ("GET", "/drop/token", None),
    ("GET", "/accounts/%s/plan_change_transactions" % ACC_B, None),
    ("GET", "/users/create_auth_jwt", None),
    ("GET", "/accounts/%s/audit?page=1&per_page=5" % ACC_B, None),
]
for method, p, body in paths:
    s, d = req(method, API + p, tok=T, body=body)
    show(method + " " + p, s, d)
