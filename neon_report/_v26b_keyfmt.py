# -*- coding: utf-8 -*-
"""dump privateKey repr + column type - determine key format"""
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
        print("cols:", cur.fetchall())
        cur.execute('SELECT "privateKey" FROM neon_auth.jwks')
        v = cur.fetchone()[0]
        print("type:", type(v))
        print("repr:", repr(v))
        print("len:", len(v))
        # try parse: json string?
        try:
            s = json.loads(v)
            print("json.loads -> type", type(s), "len", len(s))
            print("str repr:", repr(s)[:500])
        except Exception as e:
            print("not json:", e)
        cur.execute('SELECT "publicKey" FROM neon_auth.jwks')
        pv = cur.fetchone()[0]
        print("publicKey repr:", repr(pv)[:300])
