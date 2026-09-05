# -*- coding: utf-8 -*-
"""NL6: check account credit/plan + site state to understand 503 root cause"""
import http.client, ssl, json, sys
sys.path.insert(0, r'F:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B, TEAM_A, TEAM_B, SITE_A

ctx = ssl.create_default_context()


def req(method, path, token=TOKEN_A):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=25)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
         'Authorization': 'Bearer ' + token}
    conn.request(method, path, headers=h)
    r = conn.getresponse()
    raw = r.read().decode('utf-8', 'replace')
    conn.close()
    return r.status, raw


def scan(obj, keys, prefix=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if any(x in k.lower() for x in ("credit", "plan", "state", "locked", "suspend", "block", "quota")):
                if not isinstance(v, (dict, list)):
                    print("%s%s = %s" % (prefix, k, v))
            scan(v, keys, prefix + k + ".")
    elif isinstance(obj, list):
        for i, v in enumerate(obj[:5]):
            scan(v, keys, prefix + "[%d]." % i)


for tag, token, slug in (("A", TOKEN_A, TEAM_A), ("B", TOKEN_B, TEAM_B)):
    st, b = req("GET", "/api/v1/accounts/%s" % slug, token)
    print("== %s account %s -> %d" % (tag, slug, st))
    try:
        d = json.loads(b)
        for k in ("type", "plan", "name", "slug", "billing_name", "roles", "member_count", "credit_balance"):
            if k in d:
                print("   ", k, "=", d[k])
        scan(d, None)
    except Exception as e:
        print("   parse err", str(e)[:80], b[:200])
    st, b = req("GET", "/api/v1/sites/%s" % SITE_A if tag == "A" else "/api/v1/sites", token)
    print("   sites -> %d" % st)
    try:
        d = json.loads(b)
        sites = d if isinstance(d, list) else [d]
        for s in sites:
            if isinstance(s, dict):
                print("   site:", s.get("name"), "state:", s.get("state"), "plan:", s.get("plan"),
                      "locked:", s.get("locked"), "suspended:", s.get("suspended"),
                      "published_deploy:", (s.get("published_deploy") or {}).get("id", "")[:12] if s.get("published_deploy") else None)
    except Exception:
        pass
print("done")
