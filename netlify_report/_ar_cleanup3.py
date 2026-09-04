# -*- coding: utf-8 -*-
# _ar_cleanup3.py - verify cleanup state after async delete
import sys, os, json, time, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_B

API = "https://api.netlify.com/api/v1"
SITE_B = "d2977de0-d24d-4544-81cb-933e610cad7d"

def req(method, url, tok=None, timeout=30):
    r = urllib.request.Request(url, method=method)
    if tok:
        r.add_header("Authorization", "Bearer " + tok)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            b = resp.read(40000)
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

time.sleep(20)
s, d = req("GET", API + "/agent_runners?site_id=%s&per_page=10" % SITE_B, tok=TOKEN_B)
print("runs:", s)
if isinstance(d, list):
    for r in d:
        print(" ", r.get("id"), r.get("state"))
else:
    print(d)

s, d = req("GET", API + "/sites/%s/dev_servers?page=1&per_page=20" % SITE_B, tok=TOKEN_B)
print("dev servers:", s)
if isinstance(d, list):
    for ds in d:
        print(" ", ds.get("id"), ds.get("state"), ds.get("environment"))
else:
    print(json.dumps(d, ensure_ascii=False)[:600] if not isinstance(d, str) else d)

# detail of known dev server
s, d = req("GET", API + "/sites/%s/dev_servers/6a98d6d818790895d7d5ac01" % SITE_B, tok=TOKEN_B)
print("ds detail:", s)
if isinstance(d, dict):
    print(" ", {k: d.get(k) for k in ("state", "stop_reason", "done_at", "live_at", "url")})
else:
    print(d)
