# -*- coding: utf-8 -*-
"""cleanup V21-V24 leftovers: API delete + DB purge + zero-residue verify"""
import json, ssl, time, http.client

NA_HOST = "ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build"
ctx = ssl.create_default_context()
PASS = "SecTest!2026pass"


def na(method, path, body=None, cookie=None, origin="http://localhost:3000", timeout=25):
    conn = http.client.HTTPSConnection(NA_HOST, timeout=timeout, context=ctx)
    hdrs = {"Content-Type": "application/json", "Origin": origin,
            "User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    if cookie:
        hdrs["Cookie"] = cookie
    conn.request(method, path, json.dumps(body).encode() if body is not None else None, headers=hdrs)
    resp = conn.getresponse()
    data = resp.read().decode("utf-8", "replace")
    ck = resp.getheader("Set-Cookie", "")
    conn.close()
    time.sleep(0.25)
    return resp.status, data, ck


st, d, ck = na("POST", "/neondb/auth/sign-in/email",
               {"email": "libobo1229+na_org1@gmail.com", "password": PASS})
c1 = ck.split(";")[0]
st, d, ck = na("POST", "/neondb/auth/sign-in/email",
               {"email": "libobo1229+na_org2@gmail.com", "password": PASS})
c2 = ck.split(";")[0]
st, d, _ = na("GET", "/neondb/auth/organization/list", cookie=c1)
print("U1 orgs:", d[:400])
st, d, _ = na("GET", "/neondb/auth/organization/list", cookie=c2)
print("U2 orgs:", d[:400])

# DB: full picture + purge leftovers
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
        cur.execute("SELECT id, name, slug FROM neon_auth.organization")
        print("DB orgs:", cur.fetchall())
        cur.execute('SELECT id, email, status FROM neon_auth.invitation ORDER BY "createdAt"')
        print("DB invitations:", cur.fetchall())
        cur.execute('SELECT id, "organizationId", "userId", role FROM neon_auth.member')
        print("DB members:", cur.fetchall())
        # purge all test orgs (v2x names) + their rows
        cur.execute("DELETE FROM neon_auth.member WHERE \"organizationId\" IN "
                    "(SELECT id FROM neon_auth.organization WHERE name LIKE 'v2%%-org' OR name LIKE 'v2%%4%%')")
        cur.execute("DELETE FROM neon_auth.invitation WHERE \"organizationId\" IN "
                    "(SELECT id FROM neon_auth.organization WHERE name LIKE 'v2%%-org' OR name LIKE 'v2%%4%%')")
        cur.execute("DELETE FROM neon_auth.organization WHERE name LIKE 'v2%%-org' OR name LIKE 'v2%%4%%'")
        # leftover member rows for deleted orgs (cf373aa2 etc already API-deleted)
        cur.execute("DELETE FROM neon_auth.member WHERE \"organizationId\" "
                    "NOT IN (SELECT id FROM neon_auth.organization)")
        cur.execute("DELETE FROM neon_auth.invitation WHERE \"organizationId\" "
                    "NOT IN (SELECT id FROM neon_auth.organization)")
        print("purge done")
with psycopg.connect(uri2, connect_timeout=15) as dbc:
    dbc.autocommit = True
    with dbc.cursor() as cur:
        cur.execute("SELECT count(*) FROM neon_auth.organization")
        print("orgs remaining:", cur.fetchall())
        cur.execute("SELECT count(*) FROM neon_auth.member")
        print("members remaining:", cur.fetchall())
        cur.execute("SELECT count(*) FROM neon_auth.invitation")
        print("invitations remaining:", cur.fetchall())
