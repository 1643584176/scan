# -*- coding: utf-8 -*-
"""app.netlify.com functions 批量 GET 侦察(cookie A,只读)
identeer-proxy 额外试 /providers 与无 cookie"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A

ctx = ssl.create_default_context()
H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0',
     'Accept-Encoding': 'br, gzip', 'Accept': 'application/json', 'Cookie': COOKIE_A}


def get(path, cookie=True):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=30)
    h = dict(H)
    if not cookie:
        h.pop('Cookie')
    conn.request('GET', path, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    out = raw[:700].decode('utf-8', 'ignore')
    conn.close()
    return st, out


fns = ['identeer-proxy', 'identeer-proxy/providers', 'extension-proxy',
       'manage-extension-proxy', 'fetch-extensions', 'fetch-extension',
       'fetch-installed-extensions-for-team', 'fetch-relevant-installed-extensions-for-site',
       'fetch-integration-hub', 'fetch-build-plugins', 'fetch-site-configuration',
       'fetch-extension-host-site-sdk-version', 'labs-list', 'support-tickets',
       'hubspot', 'generate-bandwidth-usage-csv', 'event-observed',
       'delete-configurations-for-site', 'delete-all-team-installations-for-team',
       'install-extension', 'uninstall-extension', 'agent-runner-file-delete']
for f in fns:
    st, out = get('/.netlify/functions/' + f)
    print('%-55s [%d] %s' % (f, st, out[:160].replace('\n', ' ')))

print()
st, out = get('/.netlify/functions/identeer-proxy/providers', cookie=False)
print('%-55s [%d] %s' % ('identeer-proxy/providers (NO cookie)', st, out[:300].replace('\n', ' ')))
st, out = get('/.netlify/functions/identeer-proxy', cookie=False)
print('%-55s [%d] %s' % ('identeer-proxy (NO cookie)', st, out[:300].replace('\n', ' ')))
