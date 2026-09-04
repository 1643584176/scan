# -*- coding: utf-8 -*-
"""Netlify:内部函数面批量探测(database-query 同族)"""
import http.client, ssl, gzip, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A
ctx = ssl.create_default_context()

def req(path, method='GET', body=None):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=20)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept': 'application/json', 'Cookie': COOKIE_A,
         'Origin': 'https://app.netlify.com', 'Referer': 'https://app.netlify.com/'}
    if body is not None:
        h['Content-Type'] = 'application/json'
        body = json.dumps(body).encode()
    try:
        conn.request(method, path, body=body, headers=h)
        r = conn.getresponse(); raw = r.read()
        enc = r.getheader('Content-Encoding')
        if enc == 'gzip': raw = gzip.decompress(raw)
        st = r.status; conn.close()
        return st, raw[:220].decode('utf-8', 'replace')
    except Exception as e:
        return -1, 'ERR %s' % str(e)[:60]

FNS = ['extension-proxy', 'manage-extension-proxy', 'identeer-proxy', 'agent-runner-file-delete',
       'fetch-site-configuration', 'install-extension', 'fetch-extension', 'extensions-connections',
       'fetch-installed-extensions-for-team', 'delete-configurations-for-site', 'fetch-build-plugins',
       'verify', 'git', 'event-observed', 'fetch-extensions', 'fetch-extension-host-site-sdk-version',
       'fetch-integration-hub', 'fetch-relevant-installed-extensions-for-site']

for fn in FNS:
    p = '/.netlify/functions/%s' % fn
    s1, b1 = req(p)
    s2, b2 = req(p, method='POST', body={})
    print('%-52s GET %-3s %-90s | POST {} %-3s %s' % (fn, s1, b1.replace('\n', ' ')[:88], s2, b2.replace('\n', ' ')[:88]))
