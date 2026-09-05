# -*- coding: utf-8 -*-
"""final residue check after V27-V28"""
import json, ssl, time, http.client

ctx = ssl.create_default_context()
conn = http.client.HTTPSConnection("console-stage.neon.build", timeout=30, context=ctx)
conn.request("GET", "/api/v2/projects/orange-sun-90493739/connection_uri"
             "?database_name=neondb&role_name=neondb_owner"
             "&branch_id=br-wandering-field-w2ob6mpn",
             headers={"X-Bug-Bounty": "xxbo",
                      "Authorization": "Bearer " + json.load(open(r"F:\scan\neon_report\_apikey.json"))["key"]})
r = conn.getresponse()
uri = json.loads(r.read().decode())["uri"]
conn.close()
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
p = urlsplit(uri)
q = [(k, v) for k, v in parse_qsl(p.query) if k != "channel_binding"]
uri2 = urlunsplit((p.scheme, p.netloc, p.path, urlencode(q), p.fragment))
import psycopg
with psycopg.connect(uri2, connect_timeout=15) as dbc:
    dbc.autocommit = True
    with dbc.cursor() as cur:
        for t in ("organization", "member", "invitation"):
            cur.execute("SELECT count(*) FROM neon_auth.%s" % t)
            print("%s: %d rows" % (t, cur.fetchone()[0]))
        cur.execute("SELECT email, role, banned FROM neon_auth.user WHERE email LIKE '%%na_org%%' ORDER BY email")
        for row in cur.fetchall():
            print("user:", row)
        cur.execute("SELECT count(*) FROM neon_auth.session WHERE \"createdAt\" > now() - interval '1 hour'")
        print("recent sessions (1h): %d" % cur.fetchone()[0])
