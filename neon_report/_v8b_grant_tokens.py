# -*- coding: utf-8 -*-
"""V8b/c: (b) after explicit GRANT - Data API exposure & RLS-less row visibility
(c) verification table contents + reset-password token entropy check
(c2) request-password-reset token format/length from DB (weak token -> account takeover)"""
import json, ssl, time, http.client, random, string, re

NA_HOST = "ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build"
AP = "ep-crimson-fog-w2gucld1.apirest.us-east-2.aws.neon.build"
API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
PA = "orange-sun-90493739"
PAMAIN = "br-wandering-field-w2ob6mpn"
with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]
ctx = ssl.create_default_context()
DB_URI = None
TBL = "v8grant_" + "".join(random.choices(string.ascii_lowercase, k=6))


def out(s):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), s), flush=True)


def req(host, method, path, body=None, hdr=None, timeout=25):
    try:
        conn = http.client.HTTPSConnection(host, context=ctx, timeout=timeout)
        h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
             'Content-Type': 'application/json'}
        if hdr:
            h.update(hdr)
        conn.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=h)
        r = conn.getresponse()
        raw = r.read()
        hdrs = {k.lower(): v for k, v in r.getheaders()}
        conn.close()
        return r.status, raw.decode('utf-8', 'replace'), hdrs
    except Exception as e:
        return -1, 'EXC %s' % e, {}


def fetch_db_uri():
    global DB_URI
    st, d, _ = req(API_HOST, "GET", API_BASE + "/projects/%s/connection_uri?database_name=neondb"
                   "&role_name=neondb_owner&branch_id=%s" % (PA, PAMAIN),
                   hdr={"X-Bug-Bounty": "xxbo", "Authorization": "Bearer " + APIKEY})
    uri = json.loads(d).get("uri")
    from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
    parts = urlsplit(uri)
    q = [(k, v) for k, v in parse_qsl(parts.query) if k != "channel_binding"]
    DB_URI = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(q), parts.fragment))


def dbq(sql):
    import psycopg
    with psycopg.connect(DB_URI, connect_timeout=15) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(sql)
            if cur.description is None:
                return None
            return cur.fetchall()


def get_jwt():
    st, raw, hdrs1 = req(NA_HOST, 'POST', '/neondb/auth/sign-in/email',
                         {'email': 'libobo1229+na2@gmail.com', 'password': 'SecTest!2026pass2'},
                         {'Origin': 'http://localhost:3000'})
    sc = hdrs1.get('set-cookie') or ''
    ck = '; '.join(x.strip().split(';')[0] for x in sc.split(',') if '=' in x)
    if ck:
        st2, raw2, _ = req(NA_HOST, 'GET', '/neondb/auth/token', hdr={'Cookie': ck})
        if st2 == 200:
            return json.loads(raw2).get('token', '')
    return ""


def main():
    out("== V8b/c GRANT exposure + verification/reset token entropy ==")
    fetch_db_uri()
    jwt = get_jwt()
    out("jwt ok table=%s" % TBL)

    # ---- V8b: after explicit GRANT ----
    dbq('CREATE TABLE public.%s(id serial PRIMARY KEY, secret text, owner_tag text)' % TBL)
    dbq("INSERT INTO public.%s(secret, owner_tag) VALUES ('ROW-OWNER-U1','u1')" % TBL)
    dbq("GRANT SELECT, INSERT, UPDATE, DELETE ON public.%s TO authenticated" % TBL)
    dbq("GRANT USAGE ON SEQUENCE public.%s_id_seq TO authenticated" % TBL)
    time.sleep(2)
    for attempt in range(1, 4):
        st, d, _ = req(AP, 'GET', '/neondb/rest/v1/%s?select=*' % TBL,
                       hdr={'Authorization': 'Bearer ' + jwt})
        out("G1a JWT read grant (try %d)  -> %d %s" % (attempt, st, d[:120]))
        if st == 200:
            break
        time.sleep(5)
    st, d, _ = req(AP, 'GET', '/neondb/rest/v1/%s?select=*' % TBL,
                   hdr={'Authorization': 'Bearer ' + jwt})
    out("G1 JWT read after grant  -> %d %s" % (st, d[:200]))
    st, d, _ = req(AP, 'POST', '/neondb/rest/v1/%s' % TBL,
                   {"secret": "ROW-OTHER-USER", "owner_tag": "u2"},
                   hdr={'Authorization': 'Bearer ' + jwt, 'Prefer': 'return=representation'})
    out("G2 JWT insert by na2     -> %d %s" % (st, d[:200]))
    st, d, _ = req(AP, 'PATCH', '/neondb/rest/v1/%s?owner_tag=eq.u1' % TBL,
                   {"secret": "PATCHED-BY-NA2"},
                   hdr={'Authorization': 'Bearer ' + jwt, 'Prefer': 'return=representation'})
    out("G3 JWT update u1 row     -> %d %s" % (st, d[:200]))
    # without RLS, na2 sees/updates u1's rows (platform opt-in; host app must add RLS)
    dbq('DROP TABLE IF EXISTS public.%s' % TBL)

    # ---- V8c: verification rows after send-verification-email ----
    st, d, _ = req(NA_HOST, 'POST', '/neondb/auth/send-verification-email',
                   {'email': 'libobo1229+na2@gmail.com'}, hdr={'Origin': 'http://localhost:3000'})
    out("C1 send-verification     -> %d %s" % (st, d[:120]))
    r = dbq("SELECT id, identifier, value, \"expiresAt\", \"createdAt\" FROM neon_auth.verification "
            "WHERE identifier LIKE '%na2%' ORDER BY \"createdAt\" DESC LIMIT 5")
    out("C2 verification rows     -> %s" % ([(str(x[0])[:8], x[1], (x[2] or '')[:60], str(x[3]), str(x[4])) for x in (r or [])]))
    if r:
        tok = r[0][2] or ''
        out("C3 token len=%d chars=%s entropic=%s" % (
            len(tok),
            ''.join(sorted(set(tok)))[:30],
            len(set(tok)) >= 20 and len(tok) >= 32))

    # ---- V8c2: reset-password token from DB ----
    st, d, _ = req(NA_HOST, 'POST', '/neondb/auth/request-password-reset',
                   {'email': 'libobo1229+na2@gmail.com'}, hdr={'Origin': 'http://localhost:3000'})
    out("D1 request-password-reset -> %d %s" % (st, d[:120]))
    r = dbq("SELECT id, identifier, value, \"expiresAt\", \"createdAt\" FROM neon_auth.verification "
            "WHERE identifier LIKE '%na2%' AND (value LIKE '%reset%' OR value LIKE '%token%' OR length(value)>40) "
            "ORDER BY \"createdAt\" DESC LIMIT 5")
    for x in (r or []):
        out("D2 reset row: id=%s idtf=%s val=%s.. len=%d exp=%s" % (
            str(x[0])[:8], x[1], (x[2] or '')[:80], len(x[2] or ''), str(x[3])))
    # newest verification row overall with long value
    r2 = dbq("SELECT value FROM neon_auth.verification ORDER BY \"createdAt\" DESC LIMIT 1")
    out("D3 latest verification value len=%d head=%s" % (len(r2[0][0] or ''), (r2[0][0] or '')[:80]))
    # cleanup stale verification rows for na2 (keep env tidy)
    dbq("DELETE FROM neon_auth.verification WHERE identifier LIKE '%na2%'")
    out("cleanup verification rows removed")


if __name__ == "__main__":
    main()
