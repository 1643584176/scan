# -*- coding: utf-8 -*-
"""NL14: A-site state + self-install dblink ACL check (capability probe only, no connect/attack)"""
import http.client, ssl, json, sys
sys.path.insert(0, r'F:\scan\netlify_report')
from _net_creds import COOKIE_A, COOKIE_B, SITE_A

ctx = ssl.create_default_context()
SITE_B_ID = 'd2977de0-d24d-4544-81cb-933e610cad7d'


def q(cookie, site_id, sql):
    body = {"siteId": site_id, "action": "query", "sql": sql}
    conn = http.client.HTTPSConnection("app.netlify.com", timeout=40, context=ctx)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Content-Type': 'application/json',
         'Origin': 'https://app.netlify.com', 'Cookie': cookie}
    conn.request("POST", "/.netlify/functions/database-query", json.dumps(body).encode(), headers=h)
    r = conn.getresponse()
    raw = r.read().decode("utf-8", "replace")
    conn.close()
    return r.status, raw


def run(cookie, site, tag, sql):
    st, b = q(cookie, site, sql)
    print("== %s ==" % tag, flush=True)
    print("-> %d %s" % (st, b[:1500]), flush=True)
    return st, b


def main():
    print("== NL14 ==", flush=True)
    # 1. A site still alive? was it rebuilt too?
    run(COOKIE_A, SITE_A, "A_identity", "SELECT current_user, current_database(), oid FROM pg_database "
        "WHERE datname=current_database()")
    run(COOKIE_A, SITE_A, "A_sysid", "SELECT system_identifier FROM pg_control_system()")
    run(COOKIE_A, SITE_A, "A_exts", "SELECT extname, extowner::regrole FROM pg_extension ORDER BY 1")
    # 2. B: self-install dblink - check dblink_connect_u ACL (9/3 preinstalled version had ACL={cloud_admin=X} locked)
    run(COOKIE_B, SITE_B_ID, "B_install_dblink", "CREATE EXTENSION IF NOT EXISTS dblink")
    run(COOKIE_B, SITE_B_ID, "B_dblink_u_acl", "SELECT p.proname, p.proowner::regrole, p.prosecdef, p.proacl, "
        "pg_get_userbyid(p.proowner) FROM pg_proc p WHERE p.pronamespace::regnamespace::text='dblink' "
        "AND p.proname LIKE 'dblink_connect%' ORDER BY 1")
    run(COOKIE_B, SITE_B_ID, "B_drop_dblink", "DROP EXTENSION IF EXISTS dblink")
    run(COOKIE_B, SITE_B_ID, "B_exts_after", "SELECT count(*) FROM pg_extension")
    print("done", flush=True)


if __name__ == "__main__":
    main()
