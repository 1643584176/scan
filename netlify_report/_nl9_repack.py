# -*- coding: utf-8 -*-
"""NL9: retry database connection fetch raw + repack fix status on whichever site works"""
import http.client, ssl, json, sys
sys.path.insert(0, r'F:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B, SITE_A

ctx = ssl.create_default_context()
SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'


def get_db(token, site):
    conn = http.client.HTTPSConnection("api.netlify.com", timeout=30, context=ctx)
    conn.request("GET", "/api/v1/sites/%s/database?role=netlifydb_owner" % site,
                 headers={"Authorization": "Bearer " + token})
    r = conn.getresponse()
    raw = r.read().decode("utf-8", "replace")
    conn.close()
    print("site %s database -> %d %s" % (site, r.status, raw[:300]), flush=True)
    if r.status == 200:
        try:
            d = json.loads(raw)
            return d.get("connection_uri") or (d.get("databases") or [{}])[0].get("connection_uri")
        except Exception:
            return None
    return None


def main():
    print("== NL9 ==", flush=True)
    uri = get_db(TOKEN_A, SITE_A) or get_db(TOKEN_B, SITE_B)
    if not uri:
        print("no db uri available", flush=True)
        return
    import psycopg
    with psycopg.connect(uri, connect_timeout=20) as dbc:
        dbc.autocommit = True
        with dbc.cursor() as cur:
            cur.execute("SELECT extname FROM pg_extension ORDER BY 1")
            print("extensions:", [x[0] for x in cur.fetchall()], flush=True)
            cur.execute("SELECT nspname, nspacl FROM pg_namespace WHERE nspname='repack'")
            print("repack nspacl:", cur.fetchall(), flush=True)
            cur.execute("SELECT rolname FROM pg_roles WHERE rolname LIKE 'netlify%%' OR rolname IN ('cloud_admin','neon_superuser') ORDER BY 1")
            print("roles:", [x[0] for x in cur.fetchall()], flush=True)
            try:
                cur.execute("CREATE EXTENSION pg_repack")
                print("CREATE EXTENSION pg_repack: OK", flush=True)
                cur.execute("SELECT nspname, nspacl FROM pg_namespace WHERE nspname='repack'")
                print("repack nspacl after:", cur.fetchall(), flush=True)
                cur.execute("DROP EXTENSION pg_repack")
                print("dropped", flush=True)
            except Exception as e:
                print("CREATE EXTENSION: %s" % str(e)[:200], flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
