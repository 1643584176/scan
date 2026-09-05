# -*- coding: utf-8 -*-
"""W5a: web-access role recon (DB side + auth tables). Read-only."""
import json
import ssl
import http.client

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
PA = "orange-sun-90493739"
PAMAIN = "br-wandering-field-w2ob6mpn"
with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]

ctx = ssl.create_default_context()
conn = http.client.HTTPSConnection(API_HOST, timeout=30, context=ctx)
conn.request("GET", API_BASE + "/projects/%s/connection_uri?database_name=neondb"
             "&role_name=neondb_owner&branch_id=%s" % (PA, PAMAIN),
             headers={"X-Bug-Bounty": "xxbo", "Authorization": "Bearer " + APIKEY})
resp = conn.getresponse()
data = json.loads(resp.read().decode("utf-8", "replace"))
conn.close()
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
parts = urlsplit(data.get("uri", ""))
q = [(k, v) for k, v in parse_qsl(parts.query) if k != "channel_binding"]
DB_URI = urlunsplit((parts.scheme, parts.netloc, parts.path,
                     urlencode(q), parts.fragment))
print("uri host:", parts.hostname)

import psycopg
with psycopg.connect(DB_URI, connect_timeout=15) as c:
    c.autocommit = True
    cur = c.cursor()
    cur.execute("SELECT rolname, rolsuper, rolcanlogin, rolconnlimit FROM pg_roles "
                "WHERE rolname IN ('anonymous','web_access','neondb_owner') OR "
                "rolname LIKE '%access%' OR rolname LIKE '%web%' OR rolname LIKE '%anon%'")
    print("pg_roles:", cur.fetchall())
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='neon_auth' "
                "AND (tablename LIKE '%web%' OR tablename LIKE '%access%' "
                "OR tablename LIKE '%pass%' OR tablename LIKE '%token%' "
                "OR tablename LIKE '%session%')")
    print("auth tables web-ish:", cur.fetchall())
    # does project_config hold web access info?
    try:
        cur.execute("SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema='neon_auth' AND table_name='project_config'")
        print("project_config cols:", [r[0] for r in cur.fetchall()])
    except Exception as e:
        print("cfg cols err:", e)
    # pg_settings hints
    cur.execute("SELECT name FROM pg_settings WHERE name LIKE '%web%' OR name LIKE '%anon%' "
                "OR name LIKE '%passwordless%' OR name LIKE '%oauth%'")
    print("pg_settings hints:", cur.fetchall())
    # roles with attributes for auth users (maybe mapped)
    cur.execute("SELECT rolname FROM pg_roles WHERE rolname NOT LIKE 'pg_%' "
                "AND rolname NOT LIKE 'neon%' ORDER BY 1")
    print("custom roles:", cur.fetchall())
