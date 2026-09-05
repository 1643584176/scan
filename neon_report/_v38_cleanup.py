# -*- coding: utf-8 -*-
"""V38: cleanup v37 user + final residue check"""
import json, ssl, http.client

ctx = ssl.create_default_context()
APIKEY = json.load(open(r"F:\scan\neon_report\_apikey.json"))["key"]
PROJ = "orange-sun-90493739"
BR = "br-wandering-field-w2ob6mpn"

conn = http.client.HTTPSConnection("console-stage.neon.build", timeout=30, context=ctx)
conn.request("GET", "/api/v2/projects/%s/connection_uri?database_name=neondb&role_name=neondb_owner&branch_id=%s"
             % (PROJ, BR),
             headers={"X-Bug-Bounty": "xxbo", "Authorization": "Bearer " + APIKEY})
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
        cur.execute("DELETE FROM neon_auth.session WHERE \"userId\" IN "
                    "(SELECT id FROM neon_auth.user WHERE email LIKE 'libobo1229+v3%%')")
        cur.execute("DELETE FROM neon_auth.verification WHERE identifier LIKE 'email-verification-otp%%' "
                    "OR identifier LIKE '%%v36%%' OR identifier LIKE '%%v37%%'")
        cur.execute("DELETE FROM neon_auth.user WHERE email LIKE 'libobo1229+v3%%'")
        cur.execute("SELECT count(*) FROM neon_auth.user")
        print("users now:", cur.fetchone()[0])
        cur.execute("SELECT count(*) FROM neon_auth.session")
        print("sessions now:", cur.fetchone()[0])
        cur.execute("SELECT count(*) FROM neon_auth.verification")
        print("verifications now:", cur.fetchone()[0])
print("done")
