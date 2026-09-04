# -*- coding: utf-8 -*-
# _ar_xacct3.py - agent_runners list with site_id + hooks POST format hunt
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_A, TOKEN_B

API = "https://api.netlify.com/api/v1"
USER_A = "6a979dd2ae93f47d55b62895"
USER_B = "6a97b6454fef0db964f75db4"
SITE_A = "04f08ff6-f274-47ac-b6d7-5fb1e055f3b4"
SITE_B = "d2977de0-d24d-4544-81cb-933e610cad7d"

def req(method, url, tok=None, body=None, timeout=30):
    r = urllib.request.Request(url, method=method)
    if tok:
        r.add_header("Authorization", "Bearer " + tok)
    data = json.dumps(body).encode() if body is not None else None
    if body is not None:
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, data=data, timeout=timeout) as resp:
            b = resp.read(60000)
            try:
                return resp.status, json.loads(b.decode("utf-8", "replace"))
            except Exception:
                return resp.status, b[:300]
    except urllib.error.HTTPError as e:
        b = e.read(4000)
        try:
            return e.code, json.loads(b.decode("utf-8", "replace"))
        except Exception:
            return e.code, b[:300]
    except Exception as ex:
        return -1, str(ex)[:200]

def show(tag, s, d, cut=400):
    out = json.dumps(d, ensure_ascii=False) if not isinstance(d, str) else d
    print("%-48s -> %s %s" % (tag, s, out[:cut]))

# list with site_id (B own, B site) - baseline
show("B list site_id=B", *req("GET", API + "/agent_runners?site_id=%s&per_page=5" % SITE_B, tok=TOKEN_B))
# cross account list with site_id=A using B token
show("B list site_id=A", *req("GET", API + "/agent_runners?site_id=%s&per_page=5" % SITE_A, tok=TOKEN_B))
# user_id filter own
show("B list site_id=B user_id=B", *req("GET", API + "/agent_runners?site_id=%s&user_id=%s&per_page=5" % (SITE_B, USER_B), tok=TOKEN_B))
# user_id filter other user on same site (A user is not member of B site; expect empty or 404)
show("B list site_id=B user_id=A", *req("GET", API + "/agent_runners?site_id=%s&user_id=%s&per_page=5" % (SITE_B, USER_A), tok=TOKEN_B))
# state filter
show("B list site_id=B state=done", *req("GET", API + "/agent_runners?site_id=%s&state=done&per_page=5" % SITE_B, tok=TOKEN_B))
# hooks POST on B site (probe body shapes)
for b in ({}, {"branch": "main"}, {"site_id": SITE_B}, {"event": "deploy"}):
    show("B POST hooks %s" % str(b)[:40], *req("POST", API + "/sites/%s/agent_runner_hooks" % SITE_B, tok=TOKEN_B, body=b))
