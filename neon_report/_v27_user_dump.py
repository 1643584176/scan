# -*- coding: utf-8 -*-
"""V27: dump neon_auth user/session/account/verification - live data tables.
Questions: whose users? token format (plaintext/hash)? OAuth tokens stored?
cross-tenant residue? DB-write -> API impersonation possible?"""
import json, ssl, time, http.client

ctx = ssl.create_default_context()
import psycopg
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

conn = http.client.HTTPSConnection("console-stage.neon.build", timeout=30, context=ctx)
conn.request("GET", "/api/v2/projects/orange-sun-90493739/connection_uri"
             "?database_name=neondb&role_name=neondb_owner"
             "&branch_id=br-wandering-field-w2ob6mpn",
             headers={"X-Bug-Bounty": "xxbo",
                      "Authorization": "Bearer " + json.load(open(r"F:\scan\neon_report\_apikey.json"))["key"]})
r = conn.getresponse()
uri = json.loads(r.read().decode())["uri"]
conn.close()
p = urlsplit(uri)
q = [(k, v) for k, v in parse_qsl(p.query) if k != "channel_binding"]
uri2 = urlunsplit((p.scheme, p.netloc, p.path, urlencode(q), p.fragment))
with psycopg.connect(uri2, connect_timeout=15) as dbc:
    dbc.autocommit = True
    with dbc.cursor() as cur:
        for tbl in ("user", "session", "account", "verification"):
            cur.execute("SELECT column_name FROM information_schema.columns "
                        "WHERE table_schema='neon_auth' AND table_name=%s", (tbl,))
            cols = [x[0] for x in cur.fetchall()]
            print("\n== %s cols: %s ==" % (tbl, cols))
            cur.execute("SELECT count(*) FROM neon_auth.%s" % tbl)
            print("rows: %d" % cur.fetchone()[0])
            cur.execute("SELECT * FROM neon_auth.%s" % tbl)
            for row in cur.fetchall():
                for c, v in zip(cols, row):
                    s = str(v)
                    print("  %-16s = %s" % (c, s[:220]))
                print("  ---")
