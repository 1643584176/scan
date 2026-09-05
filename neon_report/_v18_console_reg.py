# -*- coding: utf-8 -*-
"""V18: console-stage registration unlock (2nd Keycloak account for IDOR closure).
If /api/register succeeds -> second account -> cross-account permissions/transfer tests."""
import http.client, ssl, json, time, re

HOST = 'console-stage.neon.build'
ctx = ssl.create_default_context()


def raw_req(host, method, path, headers=None, body=None, timeout=20):
    try:
        conn = http.client.HTTPSConnection(host, 443, context=ctx, timeout=timeout)
        h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
             'Accept': 'text/html,application/xhtml+xml'}
        if headers:
            h.update(headers)
        conn.request(method, path, body=body, headers=h)
        r = conn.getresponse()
        raw = r.read()
        hdrs = dict((k.lower(), v) for k, v in r.getheaders())
        st = r.status
        conn.close()
        return st, hdrs, raw.decode('utf-8', 'replace')
    except Exception as e:
        return -1, {}, 'EXC %s' % e


def out(s):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), s), flush=True)


def main():
    out("== V18 console registration ==")
    # 1. page + csrf
    st, hdrs, body = raw_req(HOST, 'GET', '/')
    csrf = ''
    for part in hdrs.get('set-cookie', '').split(','):
        kv = part.strip().split(';')[0]
        if kv.startswith('_gorilla_csrf='):
            csrf = kv.split('=', 1)[1]
    out("GET / -> %d csrf_len=%d" % (st, len(csrf)))
    ck = '_gorilla_csrf=%s' % csrf
    email = 'libobo1229+v18idr%s@gmail.com' % (str(int(time.time()))[-6:])
    # 2. register attempt
    st, hdrs, b = raw_req(HOST, 'POST', '/api/register',
                          {'Content-Type': 'application/json',
                           'Origin': 'https://console-stage.neon.build',
                           'Referer': 'https://console-stage.neon.build/',
                           'Cookie': ck, 'X-CSRF-Token': csrf},
                          json.dumps({'email': email, 'password': 'SecTest!2026pass2'}).encode())
    out("POST /api/register -> %d %s loc=%s" % (st, b[:400].replace('\n', ' '), hdrs.get('location', '')))
    # 3. keycloak register page state
    st, hdrs, b = raw_req(HOST, 'GET', '/auth/keycloak/register')
    out("GET /auth/keycloak/register -> %d loc=%s" % (st, hdrs.get('location', '')))
    # 4. keycloak direct registration endpoint probe (broker style)
    st, hdrs, b = raw_req(HOST, 'POST', '/auth/keycloak/register',
                          {'Content-Type': 'application/x-www-form-urlencoded',
                           'Origin': 'https://console-stage.neon.build',
                           'Referer': 'https://console-stage.neon.build/'},
                          'email=%s&password=SecTest!2026pass2&confirmPassword=SecTest!2026pass2' % email)
    out("POST kc/register -> %d %s loc=%s" % (st, b[:300].replace('\n', ' '), hdrs.get('location', '')))
    # 5. token endpoint for password grant (direct)
    import urllib.parse
    data = urllib.parse.urlencode({
        'grant_type': 'password', 'client_id': 'neon-console',
        'username': email, 'password': 'SecTest!2026pass2',
        'scope': 'openid profile email'})
    st, hdrs, b = raw_req(HOST, 'POST', '/realms/staging-realm/protocol/openid-connect/token',
                          {'Content-Type': 'application/x-www-form-urlencoded'}, data.encode())
    out("kc token grant -> %d %s" % (st, b[:300].replace('\n', ' ')))
    out("done")


if __name__ == "__main__":
    main()
