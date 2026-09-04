# -*- coding: utf-8 -*-
# _ar_xacct2.py - agent_runners cross-account matrix round 2 (API layer, no credits)
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_A, TOKEN_B

API = "https://api.netlify.com/api/v1"
USER_A = "6a979dd2ae93f47d55b62895"      # A user id
ACCT_A = "6a979dd2ae93f47d55b62897"      # A account id
ACCT_B = "6a97b6454fef0db964f75db6"      # B account id
SITE_A = "04f08ff6-f274-47ac-b6d7-5fb1e055f3b4"
SITE_B = "d2977de0-d24d-4544-81cb-933e610cad7d"
RID_B = "6a98d6d818790895d7d5ac00"

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

def show(tag, s, d, cut=300):
    out = json.dumps(d, ensure_ascii=False) if not isinstance(d, str) else d
    print("%-46s -> %s %s" % (tag, s, out[:cut]))

# 1. list agent_runners with user_id filter of OTHER account (B token, user_id=A user)
show("B list user_id=A-user", *req("GET", API + "/agent_runners?user_id=%s" % USER_A, tok=TOKEN_B))
# 2. B token, own list baseline
show("B list own (no filter)", *req("GET", API + "/agent_runners?page=1&per_page=5", tok=TOKEN_B))
# 3. upload_url: B token with A account_id
show("B upload_url acct=A", *req("POST", API + "/agent_runners/upload_url", tok=TOKEN_B,
     body={"account_id": ACCT_A, "content_type": "text/plain", "filename": "x.txt"}))
# 4. upload_url: B token with B account_id (baseline)
show("B upload_url acct=B", *req("POST", API + "/agent_runners/upload_url", tok=TOKEN_B,
     body={"account_id": ACCT_B, "content_type": "text/plain", "filename": "x.txt"}))
# 5. agent_runner_hooks on A site with B token
show("B hooks on A site", *req("GET", API + "/sites/%s/agent_runner_hooks" % SITE_A, tok=TOKEN_B))
show("B hooks on B site", *req("GET", API + "/sites/%s/agent_runner_hooks" % SITE_B, tok=TOKEN_B))
# 6. PATCH run (rename?) cross-account: A token patch B run - expect 404
show("A PATCH B run", *req("PATCH", API + "/agent_runners/%s" % RID_B, tok=TOKEN_A,
     body={"title": "hijack"}))
# 7. run actions cross-account: A token archive/revert/redeploy B run
show("A archive B run", *req("POST", API + "/agent_runners/%s/archive" % RID_B, tok=TOKEN_A))
show("A stop B run", *req("DELETE", API + "/agent_runners/%s" % RID_B, tok=TOKEN_A))
# 8. sessions of B run with A token
show("A sessions of B run", *req("GET", API + "/agent_runners/%s/sessions" % RID_B, tok=TOKEN_A))
# 9. answers to B run session with A token (already 404 but confirm on session endpoint w/ valid refId)
show("A answer B sess", *req("POST", API + "/agent_runners/%s/sessions/6a98d6d818790895d7d5ac02/answers" % RID_B,
     tok=TOKEN_A, body={"refId": "fe3ab820-8bae-44e9-8d7c-2f349427d727", "response": ["x"]}))
