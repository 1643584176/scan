# -*- coding: utf-8 -*-
"""cleanup: drop sec_v26 role with its grants"""
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
        cur.execute("SELECT rolname FROM pg_roles WHERE rolname LIKE 'sec_v26%'")
        roles = cur.fetchall()
        print("sec_v26 roles:", roles)
        for (rn,) in roles:
            cur.execute('REVOKE ALL ON DATABASE neondb FROM %s' % rn)
            cur.execute('REVOKE ALL ON SCHEMA neon_auth FROM %s' % rn)
            cur.execute('DROP ROLE IF EXISTS %s' % rn)
        cur.execute("SELECT rolname FROM pg_roles WHERE rolname LIKE 'sec_v26%'")
        print("remaining:", cur.fetchall())
