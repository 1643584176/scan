# -*- coding: utf-8 -*-
"""NL15: full database REST state (A/B) + B dblink self-install ACL (correct schema) + tx action liveness"""
import http.client, ssl, json, sys
sys.path.insert(0, r'F:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B, COOKIE_B, SITE_A

ctx = ssl.create_default_context()
SITE_B_ID = 'd2977de0-d24d-4544-81cb-933e610cad7d'


def api(method, path, token, body=None):
    conn = http.client.HTTPSConnection("api.netlify.com", timeout=30, context=ctx)
    h = {'Authorization': 'Bearer ' + token, 'User-Agent': 'Mozilla/5.0 Chrome/126.0',
         'Content-Type': 'application/json'}
    conn.request(method, path, json.dumps(body).encode() if body else None, headers=h)
    r = conn.getresponse()
    raw = r.read().decode("utf-8", "replace")
    conn.close()
    return r.status, raw


def dbq(sql, timeout=40):
    body = {"siteId": SITE_B_ID, "action": "query", "sql": sql}
    conn = http.client.HTTPSConnection("app.netlify.com", timeout=timeout, context=ctx)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Content-Type': 'application/json',
         'Origin': 'https://app.netlify.com', 'Cookie': COOKIE_B}
    conn.request("POST", "/.netlify/functions/database-query", json.dumps(body).encode(), headers=h)
    r = conn.getresponse()
    raw = r.read().decode("utf-8", "replace")
    conn.close()
    return r.status, raw


def main():
    print("== NL15 ==", flush=True)
    # 1. REST database state A vs B
    for tag, tok, site in (("A", TOKEN_A, SITE_A), ("B", TOKEN_B, SITE_B_ID)):
        for p in ("/api/v1/sites/%s/database", "/api/v1/sites/%s/database/branches",
                  "/api/v1/sites/%s/database/compute/settings"):
            st, b = api("GET", p % site, tok)
            print("%s GET %s -> %d %s" % (tag, p.split("{")[0].rstrip("/").split("/")[-1] or p, st, b[:250]), flush=True)
    # 2. B: dblink self-install, correct schema check
    print("== B dblink ==", flush=True)
    st, b = dbq("CREATE EXTENSION IF NOT EXISTS dblink")
    print("install -> %d %s" % (st, b[:200]), flush=True)
    st, b = dbq("SELECT p.proname, p.proowner::regrole, p.prosecdef, COALESCE(p.proacl::text,'(null)') acl, "
                "p.pronamespace::regnamespace::text nsp FROM pg_proc p WHERE p.proname LIKE 'dblink_connect%' ORDER BY 1")
    print("funcs -> %d %s" % (st, b[:1200]), flush=True)
    st, b = dbq("DROP EXTENSION IF EXISTS dblink")
    print("drop -> %d %s" % (st, b[:200]), flush=True)
    st, b = dbq("SELECT count(*) c FROM pg_extension")
    print("ext count -> %d %s" % (st, b[:200]), flush=True)
    # 3. B tx action liveness
    st, b = dbq("SELECT 1")
    print("tx? (query action above already used) -> %d %s" % (st, b[:200]), flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
