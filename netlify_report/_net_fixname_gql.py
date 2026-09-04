# -*- coding: utf-8 -*-
"""修复 SITE_A 名称(zz-hpp-rename -> 原名) + 多方向探测
A: files 上传穿越 / B: database ?role 枚举 / C: build_hooks URL 校验 / D: GraphQL 端点"""
import http.client, ssl, gzip, brotli, json, sys, re
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B

ctx = ssl.create_default_context()
SITE_A = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'

def req(method, path, body=None, token=TOKEN_A, timeout=25, ctype='application/json'):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json'}
    if body is not None:
        h['Content-Type'] = ctype
    if token: h['Authorization'] = 'Bearer ' + token
    b = json.dumps(body).encode() if (body is not None and isinstance(body, (dict, list))) else body
    conn.request(method, path, body=b, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br': raw = brotli.decompress(raw)
    elif enc == 'gzip': raw = gzip.decompress(raw)
    st = r.status
    txt = raw.decode('utf-8', 'ignore')
    conn.close()
    return st, txt

def probe(tag, m, p, body=None, tok=TOKEN_A):
    st, b = req(m, p, body, tok)
    print('%-62s %s | %s' % (tag, st, b[:220].replace('\n', ' ')))
    return st, b

print('== 0. 修复 SITE_A name ==')
st, b = req('GET', '/api/v1/sites/%s' % SITE_A)
try:
    d = json.loads(b)
    cur = d.get('name', '')
    print('current name:', cur)
    if cur.startswith('zz-hpp-'):
        st, b = probe('PATCH 恢复 name', 'PATCH', '/api/v1/sites/%s' % SITE_A,
                      {'name': 'sec-test-rcf6lz'})
except Exception as e:
    print('parse err', e, b[:200])

print()
print('== D. GraphQL 端点探测 ==')
for host in ['api.netlify.com', 'app.netlify.com']:
    for p in ['/graphql', '/api/graphql', '/api/v1/graphql', '/.netlify/graphql']:
        conn = http.client.HTTPSConnection(host, context=ctx, timeout=15)
        h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
             'Content-Type': 'application/json'}
        if host == 'api.netlify.com':
            h['Authorization'] = 'Bearer ' + TOKEN_A
        try:
            q = json.dumps({'query': '{__typename}'}).encode()
            conn.request('POST', p, body=q, headers=h)
            r = conn.getresponse()
            raw = r.read()
            enc = r.getheader('Content-Encoding')
            if enc == 'br': raw = brotli.decompress(raw)
            elif enc == 'gzip': raw = gzip.decompress(raw)
            st = r.status
            txt = raw.decode('utf-8', 'ignore')
            print('%-28s %-22s %s | %s' % (host, p, st, txt[:150].replace('\n', ' ')))
        except Exception as e:
            print('%-28s %-22s ERR %s' % (host, p, e))
        finally:
            conn.close()
print('done-part1')
