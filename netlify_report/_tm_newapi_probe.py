# -*- coding: utf-8 -*-
# _tm_newapi_probe.py - probe existence of new-feature APIs (dev_servers/agent/connect/...)
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_A, TOKEN_B, TEAM_A, SITE_A

API = "https://api.netlify.com/api/v1"

def req(method, url, tok=None, body=None, timeout=20):
    r = urllib.request.Request(url, method=method)
    if tok:
        r.add_header("Authorization", "Bearer " + tok)
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, data=data, timeout=timeout) as resp:
            b = resp.read(8000)
            try:
                return resp.status, json.loads(b.decode("utf-8", "replace"))
            except Exception:
                return resp.status, b[:400]
    except urllib.error.HTTPError as e:
        b = e.read(2000)
        try:
            return e.code, json.loads(b.decode("utf-8", "replace"))
        except Exception:
            return e.code, b[:300]
    except Exception as ex:
        return -1, str(ex)[:150]

# candidate new-feature endpoints (swagger does not list these)
candidates = [
    ("GET", "/dev_servers"),
    ("GET", "/accounts/%s/dev_servers" % TEAM_A),
    ("GET", "/sites/%s/dev_servers" % SITE_A),
    ("GET", "/agent_context"),
    ("GET", "/accounts/%s/agent_context" % TEAM_A),
    ("GET", "/connect"),
    ("GET", "/accounts/%s/connect" % TEAM_A),
    ("GET", "/sites/%s/connect" % SITE_A),
    ("GET", "/accounts/%s/logs" % TEAM_A),
    ("GET", "/sites/%s/logs" % SITE_A),
    ("GET", "/secrets"),
    ("GET", "/accounts/%s/secrets" % TEAM_A),
    ("GET", "/secrets_controller"),
    ("GET", "/ai-gateway"),
    ("GET", "/accounts/%s/ai-gateway" % TEAM_A),
    ("GET", "/organizations"),
    ("GET", "/accounts/%s/organizations" % TEAM_A),
]
for m, p in candidates:
    s, b = req(m, API + p, tok=TOKEN_A)
    msg = json.dumps(b, ensure_ascii=False)[:150] if isinstance(b, (dict, list)) else repr(b)[:120]
    print("%-5s %-45s -> %s %s" % (m, p, s, msg))
