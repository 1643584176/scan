# -*- coding: utf-8 -*-
"""V8d: Data API exposure mechanism - is schema cache refreshed by NOTIFY pgrst
or periodic? Create+grant, NOTIFY reload schema, immediate probe; if 404 wait
and probe again to detect periodic refresh."""
import json, ssl, time, http.client, random, string

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
TBL = "v8rel_" + "".join(random.choices(string.ascii_lowercase, k=6))


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
    out("== V8d Data API reload mechanism ==")
    fetch_db_uri()
    jwt = get_jwt()
    out("jwt ok table=%s" % TBL)
    dbq('CREATE TABLE public.%s(id serial PRIMARY KEY, secret text)' % TBL)
    dbq("INSERT INTO public.%s(secret) VALUES ('X')" % TBL)
    dbq("GRANT SELECT ON public.%s TO authenticated" % TBL)
    # standard PostgREST reload signal
    dbq("NOTIFY pgrst, 'reload schema'")
    out("NOTIFY pgrst reload sent")
    time.sleep(2)
    st, d, _ = req(AP, 'GET', '/neondb/rest/v1/%s?select=*' % TBL,
                   hdr={'Authorization': 'Bearer ' + jwt})
    out("P1 after NOTIFY reload  -> %d %s" % (st, d[:150]))
    if st != 200:
        for w in (20, 40):
            time.sleep(w)
            st, d, _ = req(AP, 'GET', '/neondb/rest/v1/%s?select=*' % TBL,
                           hdr={'Authorization': 'Bearer ' + jwt})
            out("P2 after +%ds           -> %d %s" % (w, st, d[:150]))
            if st == 200:
                break
    # control: owner-granted table that existed before? probe public schema listing
    st, d, _ = req(AP, 'GET', '/neondb/rest/v1/?select=*&limit=1',
                   hdr={'Authorization': 'Bearer ' + jwt})
    out("root listing           -> %d %s" % (st, d[:300]))
    dbq('DROP TABLE IF EXISTS public.%s' % TBL)
    out("cleanup done")


if __name__ == "__main__":
    main()
