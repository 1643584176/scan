# -*- coding: utf-8 -*-
"""测 neonauth sign-up 通道:无 Origin / localhost Origin(注册两个测试用户)"""
import http.client, ssl, json, time

ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'

def na_req(method, path, body=None, origin=None):
    try:
        conn = http.client.HTTPSConnection(NA, context=ctx, timeout=25)
        h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json'}
        if origin:
            h['Origin'] = origin
        conn.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=h)
        r = conn.getresponse(); raw = r.read()
        st = r.status
        sc = r.headers.get_all('Set-Cookie') if r.headers else None
        conn.close()
        return st, raw[:400], sc
    except Exception as e:
        return 0, str(e).encode()[:200], None

# 变体 1: 无 Origin
for variant, origin in [('no-origin', None), ('localhost', 'http://localhost:3000')]:
    st, raw, sc = na_req('POST', '/neondb/auth/sign-up/email',
                         {'email': 'libobo1229+na1@gmail.com', 'password': 'SecTest!2026pass', 'name': 'sec-na-1'},
                         origin=origin)
    print('[sign-up %s] -> %d | %s' % (variant, st, raw.decode(errors='replace')), flush=True)
    time.sleep(1)
