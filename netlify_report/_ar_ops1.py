# -*- coding: utf-8 -*-
# _ar_ops1.py - remaining agent_runners operation endpoints (self + cross-account)
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_A, TOKEN_B

API = "https://api.netlify.com/api/v1"
RID = "6a98d6d818790895d7d5ac00"
SID = "6a98d6d818790895d7d5ac02"

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
                return resp.status, b[:400]
    except urllib.error.HTTPError as e:
        b = e.read(8000)
        try:
            return e.code, json.loads(b.decode("utf-8", "replace"))
        except Exception:
            return e.code, b[:400]
    except Exception as ex:
        return -1, str(ex)[:200]

def show(tag, s, d, cut=500):
    out = json.dumps(d, ensure_ascii=False) if not isinstance(d, str) else d
    print("%-56s -> %s %s" % (tag, s, out[:cut]))

# self ops (B)
show("B diff", *req("GET", API + "/agent_runners/%s/diff?strip_binary=true" % RID, tok=TOKEN_B))
show("B attachments", *req("GET", API + "/agent_runners/%s/sessions/%s/attachments" % (RID, SID), tok=TOKEN_B))
show("B revert (no sess)", *req("POST", API + "/agent_runners/%s/revert" % RID, tok=TOKEN_B, body={"session_id": SID}))
show("B commit", *req("POST", API + "/agent_runners/%s/commit" % RID, tok=TOKEN_B, body={"target_branch": "main"}))
show("B pull_request", *req("POST", API + "/agent_runners/%s/pull_request" % RID, tok=TOKEN_B))
show("B publish_to_production", *req("POST", API + "/agent_runners/%s/publish_to_production" % RID, tok=TOKEN_B))
show("B rebase", *req("POST", API + "/agent_runners/%s/rebase" % RID, tok=TOKEN_B))
show("B merge_target", *req("POST", API + "/agent_runners/%s/merge_target" % RID, tok=TOKEN_B))
show("B sync_git_origin", *req("POST", API + "/agent_runners/%s/sync_git_origin" % RID, tok=TOKEN_B))
show("B redeploy sess", *req("POST", API + "/agent_runners/%s/sessions/%s/redeploy" % (RID, SID), tok=TOKEN_B))
show("B PATCH run", *req("PATCH", API + "/agent_runners/%s" % RID, tok=TOKEN_B, body={"title": "x"}))
show("B PATCH sess meta", *req("PATCH", API + "/agent_runners/%s/sessions/%s" % (RID, SID), tok=TOKEN_B, body={"meta": {}}))
show("B credit usage", *req("GET", API + "/6a97b6454fef0db964f75db6/agent_runner_credit_usage", tok=TOKEN_B))

# cross-account ops (A on B run)
show("A diff B run", *req("GET", API + "/agent_runners/%s/diff" % RID, tok=TOKEN_A))
show("A commit B run", *req("POST", API + "/agent_runners/%s/commit" % RID, tok=TOKEN_A, body={"target_branch": "main"}))
show("A publish B run", *req("POST", API + "/agent_runners/%s/publish_to_production" % RID, tok=TOKEN_A))
show("A redeploy B sess", *req("POST", API + "/agent_runners/%s/sessions/%s/redeploy" % (RID, SID), tok=TOKEN_A))
