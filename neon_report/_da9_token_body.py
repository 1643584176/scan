# -*- coding: utf-8 -*-
"""Data API 面[5b]:探 neonauth /token 的 body 格式(零破坏:仅本账号会话内换 JWT)
登录 na2 后带 cookie,尝试若干 body 形态;命中则 dump JWT header/payload。"""
import http.client, ssl, json, base64, time

ctx = ssl.create_default_context()
NA = 'ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build'

def req(method, path, body=None, raw_body=None, hdr=None, ctype='application/json'):
    conn = http.client.HTTPSConnection(NA, context=ctx, timeout=20)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
    if hdr: h.update(hdr)
    payload = None
    if raw_body is not None:
        payload = raw_body
        if ctype:
            h['Content-Type'] = ctype
    elif body is not None:
        payload = json.dumps(body).encode()
        h['Content-Type'] = ctype
    conn.request(method, path, body=payload, headers=h)
    r = conn.getresponse(); raw = r.read(); st = r.status
    conn.close()
    return st, raw

def b64u_dec(s):
    s = s.replace('-', '+').replace('_', '/')
    s += '=' * (-len(s) % 4)
    return base64.b64decode(s)

# 1) 登录 na2 拿 cookie
st, raw, = req('POST', '/neondb/auth/sign-in/email',
               {'email': 'libobo1229+na2@gmail.com', 'password': 'SecTest!2026pass2'},
               hdr={'Origin': 'http://localhost:3000'})
print('sign-in:', st)
# 重新拿 cookie(需捕获 Set-Cookie)
conn = http.client.HTTPSConnection(NA, context=ctx, timeout=20)
h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json',
     'Origin': 'http://localhost:3000'}
conn.request('POST', '/neondb/auth/sign-in/email',
             json.dumps({'email': 'libobo1229+na2@gmail.com', 'password': 'SecTest!2026pass2'}).encode(), headers=h)
r = conn.getresponse(); raw = r.read(); st = r.status
sc = r.headers.get_all('Set-Cookie') or []
conn.close()
ck = '; '.join(c.split(';')[0] for c in sc)
print('login status:', st, '| cookies:', len(sc))
if not ck:
    print('NO COOKIE, abort'); raise SystemExit
print('cookie head:', ck[:60], '...')

sess = None
try:
    d = json.loads(raw)
    sess = d.get('token') or (d.get('session') or {}).get('token')
except Exception:
    pass

def show(name, st, raw):
    print('\n[%s] -> %d' % (name, st))
    s = raw.decode(errors='replace')
    print(' ', s[:400].replace('\n', ' '))
    if st == 200:
        try:
            d = json.loads(raw)
            tok = d.get('token') or d.get('jwt') or ''
            if tok and tok.count('.') == 2:
                p = tok.split('.')
                print('  header:', json.dumps(json.loads(b64u_dec(p[0]))))
                print('  payload:', json.dumps(json.loads(b64u_dec(p[1])), ensure_ascii=False))
        except Exception as e:
            print('  parse err:', e)

# 2) 各种 body 形态
forms = [
    ('json {}', {'body': {}}),
    ('json {"session": tok}', {'body': {'session': sess}}),
    ('json {"token": tok}', {'body': {'token': sess}}),
    ('json {"sessionToken": tok}', {'body': {'sessionToken': sess}}),
    ('no-ctype empty', {'raw_body': b''}),
    ('json empty via raw', {'raw_body': b'{}', 'ctype': 'application/json'}),
]
for name, kw in forms:
    hdr = {'Cookie': ck, 'Authorization': 'Bearer ' + (sess or '')}
    if kw.get('raw_body') is not None:
        st, raw = req('POST', '/neondb/auth/token', raw_body=kw['raw_body'], hdr=hdr,
                      ctype=kw.get('ctype', 'application/json'))
    else:
        st, raw = req('POST', '/neondb/auth/token', body=kw['body'], hdr=hdr)
    show(name, st, raw)
    time.sleep(0.3)

# 3) GET /token 变体
st, raw = req('GET', '/neondb/auth/token', hdr={'Cookie': ck})
show('GET /token with cookie', st, raw)
st, raw = req('GET', '/neondb/auth/token?database=neondb', hdr={'Cookie': ck})
show('GET /token?database=neondb', st, raw)
