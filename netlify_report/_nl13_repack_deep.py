# -*- coding: utf-8 -*-
"""NL13: deep fix-status check - reinstall pg_repack, inspect SECURITY DEFINER funcs + db identity"""
import http.client, ssl, json, sys
sys.path.insert(0, r'F:\scan\netlify_report')
from _net_creds import COOKIE_B

ctx = ssl.create_default_context()
SITE_B_ID = 'd2977de0-d24d-4544-81cb-933e610cad7d'


def q(sql):
    body = {"siteId": SITE_B_ID, "action": "query", "sql": sql}
    conn = http.client.HTTPSConnection("app.netlify.com", timeout=40, context=ctx)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Content-Type': 'application/json',
         'Origin': 'https://app.netlify.com', 'Cookie': COOKIE_B}
    conn.request("POST", "/.netlify/functions/database-query", json.dumps(body).encode(), headers=h)
    r = conn.getresponse()
    raw = r.read().decode("utf-8", "replace")
    conn.close()
    return r.status, raw


def run(tag, sql):
    st, b = q(sql)
    print("== %s ==" % tag, flush=True)
    print("-> %d %s" % (st, b[:2000]), flush=True)
    return st, b


def main():
    print("== NL13 ==", flush=True)
    # db identity - is this the same database as 9/3 (fresh DB oid 24614)?
    run("dbid", "SELECT current_database(), oid, datname, pg_size_pretty(pg_database_size(oid)) "
                "FROM pg_database WHERE datname=current_database()")
    run("sysid", "SELECT system_identifier FROM pg_control_system()")
    # install + inspect definer funcs
    run("install", "CREATE EXTENSION IF NOT EXISTS pg_repack")
    run("repack_definer", "SELECT p.proname, p.proowner::regrole, p.prosecdef, p.proacl "
                          "FROM pg_proc p WHERE p.pronamespace::regnamespace::text='repack' AND p.prosecdef ORDER BY 1")
    run("repack_trigger_def", "SELECT pg_get_functiondef(p.oid) FROM pg_proc p "
                              "WHERE p.pronamespace::regnamespace::text='repack' AND p.proname='repack_trigger'")
    run("schema_acl", "SELECT nspname, nspacl FROM pg_namespace WHERE nspname='repack'")
    run("log_tbl_acl", "SELECT tablename, tableowner FROM pg_tables WHERE schemaname='repack' ORDER BY 1")
    # does the fix validate the log-table owner? check repack_trigger body via pg_get_functiondef (above)
    run("drop_ext", "DROP EXTENSION pg_repack")
    run("confirm_gone", "SELECT count(*) FROM pg_extension WHERE extname='pg_repack'")
    print("done", flush=True)


if __name__ == "__main__":
    main()
