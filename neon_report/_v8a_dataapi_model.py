# -*- coding: utf-8 -*-
"""V8a: Data API data-exposure model - create real table, then probe access
with: (1) authenticated JWT, (2) no auth, (3) role=anonymous param, (4) anon-style.
Determines whether Neon Data API defaults to open (no RLS -> readable by any
signed-up user) or requires explicit exposure."""
import json, ssl, time, http.client, base64, random, string

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
TBL = "v8probe_" + "".join(random.choices(string.ascii_lowercase, k=6))


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


def dbq(sql, fetch=True):
    import psycopg
    with psycopg.connect(DB_URI, connect_timeout=15) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(sql)
            if cur.description is None:
                return None
            return cur.fetchall() if fetch else None


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
    out("== V8a Data API exposure model ==")
    fetch_db_uri()
    jwt = get_jwt()
    out("jwt len=%d table=%s" % (len(jwt), TBL))

    # create table + row as owner; DEFAULT grants (no explicit grant)
    dbq('CREATE TABLE public.%s(id serial PRIMARY KEY, secret text)' % TBL)
    dbq("INSERT INTO public.%s(secret) VALUES ('TOP-SECRET-ROW')" % TBL)
    # check default privileges quickly
    r = dbq("SELECT grantee, privilege_type FROM information_schema.role_table_grants "
            "WHERE table_name=%s AND table_schema='public'" % ("'" + TBL + "'"))
    out("grants: %s" % r)

    # probe 1: authenticated JWT read
    st, d, _ = req(AP, 'GET', '/neondb/rest/v1/%s?select=*' % TBL,
                   hdr={'Authorization': 'Bearer ' + jwt})
    out("A JWT read            -> %d %s" % (st, d[:200]))
    # probe 2: no auth
    st, d, _ = req(AP, 'GET', '/neondb/rest/v1/%s?select=*' % TBL)
    out("B no-auth read        -> %d %s" % (st, d[:200]))
    # probe 3: role=anonymous query param (Supabase anon style)
    st, d, _ = req(AP, 'GET', '/neondb/rest/v1/%s?select=*&role=anonymous' % TBL)
    out("C role=anonymous      -> %d %s" % (st, d[:200]))
    # probe 4: JWT write (insert)
    st, d, _ = req(AP, 'POST', '/neondb/rest/v1/%s' % TBL,
                   {"secret": "INSERTED-VIA-DATAAPI"}, hdr={'Authorization': 'Bearer ' + jwt})
    out("D JWT insert          -> %d %s" % (st, d[:200]))
    # probe 5: JWT update/delete
    st, d, _ = req(AP, 'PATCH', '/neondb/rest/v1/%s?id=eq.1' % TBL,
                   {"secret": "PATCHED"}, hdr={'Authorization': 'Bearer ' + jwt,
                                               'Prefer': 'return=representation'})
    out("E JWT update          -> %d %s" % (st, d[:200]))
    st, d, _ = req(AP, 'DELETE', '/neondb/rest/v1/%s?id=eq.2' % TBL,
                   hdr={'Authorization': 'Bearer ' + jwt})
    out("F JWT delete row2     -> %d %s" % (st, d[:200]))

    # verify DB state after probes
    r = dbq('SELECT id, secret FROM public.%s ORDER BY id' % TBL)
    out("DB rows after probes: %s" % r)

    # cleanup
    dbq('DROP TABLE IF EXISTS public.%s' % TBL)
    out("cleanup dropped %s" % TBL)


if __name__ == "__main__":
    main()
