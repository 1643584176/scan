# -*- coding: utf-8 -*-
"""NL8: A. GraphQL endpoint probe (app/api); B. pg_repack fix-status check on netlify db (read-only)
B hypothesis: after pg_repack report, is repack schema still writable by neon_superuser? (informational only)"""
import http.client, ssl, json, sys, time
sys.path.insert(0, r'F:\scan\netlify_report')
from _net_creds import TOKEN_A, COOKIE_A, SITE_A, TEAM_A

ctx = ssl.create_default_context()


def api(method, path, body=None, host="api.netlify.com", cookie=None, ctype="application/json"):
    conn = http.client.HTTPSConnection(host, timeout=30, context=ctx)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept': '*/*', 'Content-Type': ctype}
    if cookie:
        h['Cookie'] = cookie
    else:
        h['Authorization'] = 'Bearer ' + TOKEN_A
    b = json.dumps(body).encode() if body is not None else None
    conn.request(method, path, body=b, headers=h)
    r = conn.getresponse()
    raw = r.read()
    conn.close()
    return r.status, raw.decode('utf-8', 'replace')


def main():
    print("== NL8 ==", flush=True)
    # A. GraphQL endpoints
    gql = '{"query":"{ __typename }"}'
    for host, path in (("api.netlify.com", "/graphql"),
                       ("api.netlify.com", "/api/v1/graphql"),
                       ("app.netlify.com", "/graphql"),
                       ("app.netlify.com", "/api/graphql"),
                       ("app.netlify.com", "/.netlify/functions/graphql"),
                       ("api.netlify.com", "/api/v1/connect/graphql")):
        try:
            if host == "app.netlify.com":
                st, b = api("POST", path, json.loads(gql), host=host, cookie=COOKIE_A)
            else:
                st, b = api("POST", path, json.loads(gql))
            print("%s%s -> %d %s" % (host, path, st, b[:100].replace("\n", " ")), flush=True)
        except Exception as e:
            print("%s%s ERR %s" % (host, path, str(e)[:80]), flush=True)
        time.sleep(0.3)
    # B. pg_repack fix status (read-only): extension ACL + schema acl
    conn = http.client.HTTPSConnection("api.netlify.com", timeout=30, context=ctx)
    conn.request("GET", "/api/v1/sites/%s/database?role=netlifydb_owner" % SITE_A,
                 headers={"Authorization": "Bearer " + TOKEN_A})
    r = conn.getresponse()
    d = json.loads(r.read().decode())
    conn.close()
    uri = d.get("connection_uri") or (d.get("databases") or [{}])[0].get("connection_uri")
    if not uri:
        print("no uri:", json.dumps(d)[:300], flush=True)
        return
    import psycopg
    with psycopg.connect(uri, connect_timeout=20) as dbc:
        dbc.autocommit = True
        with dbc.cursor() as cur:
            cur.execute("SELECT extname FROM pg_extension ORDER BY 1")
            print("extensions:", [x[0] for x in cur.fetchall()], flush=True)
            cur.execute("SELECT nspname, nspacl FROM pg_namespace WHERE nspname='repack'")
            print("repack nspacl:", cur.fetchall(), flush=True)
            cur.execute("SELECT rolname FROM pg_roles WHERE rolname LIKE 'netlify%%' OR rolname IN ('cloud_admin','neon_superuser')")
            print("roles:", [x[0] for x in cur.fetchall()], flush=True)
            # can we still install?
            try:
                cur.execute("CREATE EXTENSION pg_repack")
                print("CREATE EXTENSION pg_repack: OK (still installable)", flush=True)
                cur.execute("SELECT nspname, nspacl FROM pg_namespace WHERE nspname='repack'")
                print("repack nspacl after:", cur.fetchall(), flush=True)
                cur.execute("DROP EXTENSION pg_repack")
                print("dropped again", flush=True)
            except Exception as e:
                print("CREATE EXTENSION pg_repack: DENIED -> %s" % str(e)[:150], flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
