# -*- coding: utf-8 -*-
"""V18b: register retry with proper csrf from /login page flow."""
import http.client, ssl, json, time

HOST = 'console-stage.neon.build'
ctx = ssl.create_default_context()


def raw_req(method, path, headers=None, body=None, timeout=20):
    try:
        conn = http.client.HTTPSConnection(HOST, 443, context=ctx, timeout=timeout)
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


def parse_ck(ck):
    return {x.strip().split(';')[0].split('=', 1)[0]: x.strip().split(';')[0].split('=', 1)[1]
            for x in ck.split(',') if '=' in x}


def main():
    out("== V18b register with login-page csrf ==")
    email = 'libobo1229+v18idr%s@gmail.com' % (str(int(time.time()))[-6:])
    # follow login page
    st, hdrs, body = raw_req('GET', '/login')
    out("GET /login -> %d loc=%s" % (st, hdrs.get('location', '')))
    cookies = parse_ck(hdrs.get('set-cookie', ''))
    csrf = cookies.get('_gorilla_csrf', '')
    out("csrf len=%d keys=%s" % (len(csrf), list(cookies.keys())))
    if not csrf:
        out("no csrf; abort")
        return
    ck = '_gorilla_csrf=%s' % csrf
    for i in range(2):
        st, hdrs, b = raw_req('POST', '/api/register',
                              {'Content-Type': 'application/json',
                               'Origin': 'https://console-stage.neon.build',
                               'Referer': 'https://console-stage.neon.build/login',
                               'Cookie': ck,
                               'X-CSRF-Token': csrf,
                               'X-Csrf-Token': csrf,
                               'Csrf-Token': csrf},
                              json.dumps({'email': email, 'password': 'SecTest!2026pass2'}).encode())
        out("attempt %d -> %d %s loc=%s" % (i, st, b[:400].replace('\n', ' '), hdrs.get('location', '')))
        if st == 200:
            break
        time.sleep(1)
        # refresh csrf
        st2, hdrs2, _ = raw_req('GET', '/login')
        cookies2 = parse_ck(hdrs2.get('set-cookie', ''))
        if cookies2.get('_gorilla_csrf'):
            csrf = cookies2['_gorilla_csrf']
            ck = '_gorilla_csrf=%s' % csrf
    # also try gorilla style header
    out("done")


if __name__ == "__main__":
    main()
