# -*- coding: utf-8 -*-
"""V31c: plugin_configs full JSON + v29iso branch project_config + auth-domain admin/config endpoints"""
import json, ssl, time, http.client

ctx = ssl.create_default_context()
APIKEY = json.load(open(r"F:\scan\neon_report\_apikey.json"))["key"]
PROJ = "orange-sun-90493739"
BR = "br-wandering-field-w2ob6mpn"


def out(s):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), s), flush=True)


def db_uri(branch=BR):
    conn = http.client.HTTPSConnection("console-stage.neon.build", timeout=30, context=ctx)
    conn.request("GET", "/api/v2/projects/%s/connection_uri?database_name=neondb&role_name=neondb_owner&branch_id=%s"
                 % (PROJ, branch),
                 headers={"X-Bug-Bounty": "xxbo", "Authorization": "Bearer " + APIKEY})
    r = conn.getresponse()
    uri = json.loads(r.read().decode())["uri"]
    conn.close()
    from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
    p = urlsplit(uri)
    q = [(k, v) for k, v in parse_qsl(p.query) if k != "channel_binding"]
    return urlunsplit((p.scheme, p.netloc, p.path, urlencode(q), p.fragment))


def main():
    out("== V31c ==")
    import psycopg
    with psycopg.connect(db_uri(), connect_timeout=15) as dbc:
        dbc.autocommit = True
        with dbc.cursor() as cur:
            cur.execute("SELECT plugin_configs FROM neon_auth.project_config")
            pc = cur.fetchone()[0]
            out("plugin_configs full:")
            out(json.dumps(pc, indent=1, ensure_ascii=False)[:2500])
    # v29iso branch project_config
    try:
        with psycopg.connect(db_uri("br-raspy-snow-w2n12fvw"), connect_timeout=15) as dbc:
            dbc.autocommit = True
            with dbc.cursor() as cur:
                cur.execute("SELECT endpoint_id, \"createdAt\" FROM neon_auth.project_config")
                for row in cur.fetchall():
                    out("branch pc: endpoint_id=%s created=%s" % row)
    except Exception as ex:
        out("branch db err: %s" % ex)
    # auth-domain admin/config endpoints
    NA = "ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build"
    for pth in ("/neondb/auth/config", "/neondb/auth/settings", "/neondb/auth/admin/config",
                "/neondb/auth/admin/settings", "/neondb/auth/admin/update-config",
                "/neondb/auth/.well-known/openid-configuration"):
        conn = http.client.HTTPSConnection(NA, timeout=20, context=ctx)
        conn.request("GET", pth, headers={"Origin": "http://localhost:3000", "User-Agent": "Mozilla/5.0"})
        r = conn.getresponse()
        d = r.read().decode("utf-8", "replace")
        conn.close()
        out("GET %-45s -> %d %s" % (pth, r.status, d[:100]))
        time.sleep(0.2)
    out("done")


if __name__ == "__main__":
    main()
