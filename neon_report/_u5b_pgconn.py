# -*- coding: utf-8 -*-
"""Fetch connection uri w/ password, then real connect via pg8000:
- ep-* direct host
- pg.neon.tech (passwordless domain)
- with/without ssl
"""
import json
import ssl
import http.client
import pg8000.dbapi

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
HB = {"X-Bug-Bounty": "xxbo"}
PA = "orange-sun-90493739"
LOG = r"F:\scan\neon_report\_u5b_out.txt"

with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]


def call(method, path, body=None, timeout=30):
    ctx = ssl.create_default_context()
    conn = http.client.HTTPSConnection(API_HOST, timeout=timeout, context=ctx)
    payload = json.dumps(body) if body is not None else None
    hdrs = dict(HB, Authorization="Bearer " + APIKEY)
    if body is not None:
        hdrs["Content-Type"] = "application/json"
    conn.request(method, API_BASE + path, body=payload, headers=hdrs)
    resp = conn.getresponse()
    data = resp.read().decode("utf-8", "replace")
    conn.close()
    return resp.status, data


def out(s):
    print(s, flush=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(s + "\n")


uri = None
for q in ("database_name=neondb", "database_name=neondb&role_name=neondb_owner",
          "database_name=neondb&branch_id=br-wandering-field-w2ob6mpn"):
    st, d = call("GET", "/projects/%s/connection_uri?%s" % (PA, q))
    out("== connuri %s -> %s" % (q, st))
    if st == 200:
        uri = json.loads(d).get("uri")
        break
    out("    %s" % d[:300])

if not uri:
    out("no uri")
else:
    # sanitize output (password is ours)
    out("== URI (password redacted check): %s" % uri)
    from urllib.parse import urlsplit, parse_qs
    u = urlsplit(uri)
    pw = u.password
    user = u.username
    db = u.path.lstrip("/")
    host = u.hostname
    port = u.port or 5432
    out("user=%s db=%s host=%s port=%s pwlen=%d" % (user, db, host, port, len(pw or "")))

    for h, tag in ((host, "EP-HOST"), ("pg.neon.tech", "PG.NEON.TECH")):
        for sslmode, stag in (("require", "ssl"), (None, "nossl")):
            kw = dict(host=h, user=user, password=pw, database=db, port=port,
                      timeout=12)
            if sslmode:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                kw["ssl_context"] = ctx
            try:
                conn = pg8000.dbapi.connect(**kw)
                cur = conn.cursor()
                cur.execute("select current_user, current_database(), version()")
                row = cur.fetchone()
                out("*** CONNECT OK %s %s: %r" % (tag, stag, row))
                conn.close()
                break
            except Exception as e:
                out("    %s %s fail: %s: %s" % (tag, stag, type(e).__name__, str(e)[:220]))
print("== DONE", flush=True)
