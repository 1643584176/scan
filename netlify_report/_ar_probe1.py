# -*- coding: utf-8 -*-
# _ar_probe1.py - agent_runners REST surface on B (has credits)
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_A, TOKEN_B

API = "https://api.netlify.com/api/v1"
SITE_B = "d2977de0-d24d-4544-81cb-933e610cad7d"
SITE_A = "04f08ff6-f274-47ac-b6d7-5fb1e055f3b4"

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
                return resp.status, b[:800]
    except urllib.error.HTTPError as e:
        b = e.read(8000)
        try:
            return e.code, json.loads(b.decode("utf-8", "replace"))
        except Exception:
            return e.code, b[:600]
    except Exception as ex:
        return -1, str(ex)[:200]

def show(tag, s, d):
    if isinstance(d, bytes):
        d = d.decode("utf-8", "replace")
    if isinstance(d, str):
        print("%-40s -> %s %s" % (tag, s, d[:400]))
    else:
        print("%-40s -> %s %s" % (tag, s, json.dumps(d, ensure_ascii=False)[:400]))

# 1) list agent runners on B site (B token), A site cross
show("B list own site", *req("GET", API + "/agent_runners?site_id=%s&per_page=5" % SITE_B, tok=TOKEN_B))
show("B list A site", *req("GET", API + "/agent_runners?site_id=%s&per_page=5" % SITE_A, tok=TOKEN_B))
show("A list A site", *req("GET", API + "/agent_runners?site_id=%s&per_page=5" % SITE_A, tok=TOKEN_A))
show("anon list", *req("GET", API + "/agent_runners?site_id=%s&per_page=5" % SITE_B))
# 2) upload_url
show("B upload_url", *req("POST", API + "/agent_runners/upload_url", tok=TOKEN_B, body={}))
show("A upload_url", *req("POST", API + "/agent_runners/upload_url", tok=TOKEN_A, body={}))
# 3) minimal create attempt
show("B create minimal", *req("POST", API + "/agent_runners?site_id=%s" % SITE_B, tok=TOKEN_B,
                              body={"prompt": "list files in the repository" }))
show("B create w/agent", *req("POST", API + "/agent_runners?site_id=%s" % SITE_B, tok=TOKEN_B,
                              body={"prompt": "hello", "agent": "koda", "model": "default", "mode": "standard"}))
# 4) status endpoint
show("B status", *req("GET", API + "/agent_runners/status", tok=TOKEN_B))
