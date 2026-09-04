# -*- coding: utf-8 -*-
# _devsrv1.py - dev_servers REST matrix (list/detail/lookup cross-account)
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_A, TOKEN_B

API = "https://api.netlify.com/api/v1"
SITE_A = "04f08ff6-f274-47ac-b6d7-5fb1e055f3b4"
SITE_B = "d2977de0-d24d-4544-81cb-933e610cad7d"
DS_B = "6a98d6d818790895d7d5ac01"  # dev server id from agent session

def req(method, url, tok=None, body=None, timeout=30):
    r = urllib.request.Request(url, method=method)
    if tok:
        r.add_header("Authorization", "Bearer " + tok)
    data = json.dumps(body).encode() if body is not None else None
    if body is not None:
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, data=data, timeout=timeout) as resp:
            b = resp.read(80000)
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

def show(tag, s, d, cut=600):
    out = json.dumps(d, ensure_ascii=False) if not isinstance(d, str) else d
    print("%-52s -> %s %s" % (tag, s, out[:cut]))

# 1. B list dev servers on own site
show("B list dev_servers B site", *req("GET", API + "/sites/%s/dev_servers?page=1&per_page=20" % SITE_B, tok=TOKEN_B))
# 2. cross-account list (B token on A site)
show("B list dev_servers A site", *req("GET", API + "/sites/%s/dev_servers?page=1&per_page=20" % SITE_A, tok=TOKEN_B))
# 3. B detail of own dev server
show("B dev_server detail", *req("GET", API + "/sites/%s/dev_servers/%s" % (SITE_B, DS_B), tok=TOKEN_B))
# 4. cross-account detail (A token on B dev server)
show("A dev_server detail B", *req("GET", API + "/sites/%s/dev_servers/%s" % (SITE_B, DS_B), tok=TOKEN_A))
# 5. lookup endpoint shapes (POST /dev_servers/lookup?domain=)
show("lookup no domain", *req("POST", API + "/dev_servers/lookup", tok=TOKEN_B))
show("lookup domain B site", *req("POST", API + "/dev_servers/lookup?domain=%s" % "sec-b-08v4pk.netlify.app", tok=TOKEN_B))
show("lookup domain example", *req("POST", API + "/dev_servers/lookup?domain=%s" % "example.com", tok=TOKEN_B))
show("lookup anon", *req("POST", API + "/dev_servers/lookup?domain=%s" % "sec-b-08v4pk.netlify.app"))
# 6. active dev servers
show("B active dev_servers", *req("GET", API + "/sites/%s/dev_servers/active" % SITE_B, tok=TOKEN_B))
show("A active dev_servers B site", *req("GET", API + "/sites/%s/dev_servers/active" % SITE_B, tok=TOKEN_A))
# 7. dev_server_hooks
show("B dev_server_hooks", *req("GET", API + "/sites/%s/dev_server_hooks" % SITE_B, tok=TOKEN_B))
show("B dev_server_hooks A site", *req("GET", API + "/sites/%s/dev_server_hooks" % SITE_A, tok=TOKEN_B))
