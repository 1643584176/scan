# -*- coding: utf-8 -*-
"""fetch-extensions 完整记录结构(找 hostSiteUrl/安装要求)"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A

TEAM_A = '6a979dd2ae93f47d55b62897'
ctx = ssl.create_default_context()


def fn(method, path):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=30)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json', 'Cookie': COOKIE_A}
    conn.request(method, path, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    out = raw.decode('utf-8', 'ignore')
    conn.close()
    return st, out

st, out = fn('GET', '/.netlify/functions/fetch-extensions?teamId=%s' % TEAM_A)
data = json.loads(out)
print('总数:', len(data))
for ext in data[:5]:
    print(json.dumps(ext, indent=1)[:1200])
    print('---')
