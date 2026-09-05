# -*- coding: utf-8 -*-
"""diag: Set-Cookie vs body token vs DB session row"""
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
    hd = dict((k.lower(), v) for k, v in resp.getheaders())
    conn.close()
    time.sleep(0.25)
    return resp.status, data, hd


st, d, hd = na("POST", "/neondb/auth/sign-in/email",
               {"email": "libobo1229+na_org2@gmail.com", "password": PASS})
print("sign-in", st)
body_tok = json.loads(d).get("token")
print("body token:", body_tok)
sc = hd.get("set-cookie", "")
print("Set-Cookie:", sc[:200])
# cookie name + value from Set-Cookie
first = sc.split(",")[0].strip() if sc else ""
print("first cookie:", first[:120])
name, val = first.split(";")[0].split("=", 1)
print("cookie name=%r val=%r" % (name, val))
print("body==cookie val:", body_tok == val)
# use Set-Cookie cookie -> API
st2, d2, _ = na("GET", "/neondb/auth/get-session", cookie=first.split(";")[0])
print("get-session with set-cookie cookie:", st2, d2[:150])
st3, d3, _ = na("GET", "/neondb/auth/organization/list", cookie=first.split(";")[0])
print("org/list with set-cookie cookie:", st3, d3[:100])
# DB: count sessions for U2 and list newest tokens
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
        cur.execute('SELECT token, "createdAt" FROM neon_auth.session WHERE "userId"=\'66b42c6b-c41e-4c5a-a2fa-aa5957cfaec0\' ORDER BY "createdAt" DESC LIMIT 4')
        for t, c in cur.fetchall():
            print("DB token:", t, "match-cookie:", t == val, "match-body:", t == body_tok)
