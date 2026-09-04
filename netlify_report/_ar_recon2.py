# -*- coding: utf-8 -*-
# _ar_recon2.py - final agent run: network egress + env var presence (SET/UNSET only)
import sys, os, json, time, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _net_creds import TOKEN_B

API = "https://api.netlify.com/api/v1"
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
            b = resp.read(80000)
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

prompt = ("I am debugging a network connectivity issue in this project's build "
          "environment (outbound HTTPS requests intermittently fail). Please run these "
          "diagnostics and report outputs verbatim:\n"
          "1) curl -sS -m 12 -o /dev/null -w 'example.com HTTP %{http_code}\\n' https://example.com\n"
          "2) curl -sS -m 12 -I https://api.netlify.com/api/v1/ 2>&1 | head -8\n"
          "3) For each of the following variable names, report only SET or UNSET (never print any value): "
          "NETLIFY_AUTH_TOKEN, NETLIFY_ACCESS_TOKEN, NETLIFY_API_URL, NETLIFY_SITE_ID, "
          "AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN, DATABASE_URL, HOME, USER, PATH\n"
          "If a tool is unavailable, say which commands you could not run.")

s, d = req("POST", API + "/agent_runners?site_id=%s" % SITE_B, tok=TOKEN_B,
           body={"prompt": prompt})
if isinstance(d, dict) and d.get("id"):
    rid = d["id"]
    print("created:", rid, "state:", d.get("state"))
    json.dump({"rid": rid}, open(r"D:\scan\netlify_report\_ar_recon2_rid.json", "w"))
    for i in range(40):
        time.sleep(8)
        s2, dd = req("GET", API + "/agent_runners/%s" % rid, tok=TOKEN_B)
        st = dd.get("state") if isinstance(dd, dict) else None
        print("poll %d: state=%s" % (i, st), flush=True)
        if st in ("done", "failed", "error", "stopped", "cancelled"):
            break
else:
    print("create failed:", s, json.dumps(d, ensure_ascii=False)[:400] if not isinstance(d, str) else d[:300])
