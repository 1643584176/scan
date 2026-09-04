# -*- coding: utf-8 -*-
"""扩展接口交叉矩阵(A cookie + B team/site)"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A

TEAM_A = '6a979dd2ae93f47d55b62897'
TEAM_B = '6a97b6454fef0db964f75db6'
SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
ctx = ssl.create_default_context()


def fn(method, path, body=None, cookie=COOKIE_A, rawlen=400):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=30)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json'}
    if cookie:
        h['Cookie'] = cookie
    b = json.dumps(body).encode() if body is not None else None
    conn.request(method, path, body=b, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    out = raw[:rawlen].decode('utf-8', 'ignore')
    conn.close()
    return st, out


cases = [
    # fetch-extensions:自己 vs 交叉
    ('fetch-ext A team  ', 'GET', '/.netlify/functions/fetch-extensions?teamId=%s' % TEAM_A, None),
    ('fetch-ext B team  ', 'GET', '/.netlify/functions/fetch-extensions?teamId=%s' % TEAM_B, None),
    # fetch-extension(slug):team 交叉
    ('fetch-ext xyz A   ', 'GET', '/.netlify/functions/fetch-extension?slug=xyz&teamId=%s' % TEAM_A, None),
    ('fetch-ext xyz B   ', 'GET', '/.netlify/functions/fetch-extension?slug=xyz&teamId=%s' % TEAM_B, None),
    # extension-proxy:slug=integration-host-site/{site}
    ('ext-proxy siteB   ', 'GET', '/.netlify/functions/extension-proxy?teamId=%s&slug=integration-host-site/%s' % (TEAM_A, SITE_B), None),
    ('ext-proxy xyz     ', 'GET', '/.netlify/functions/extension-proxy?teamId=%s&slug=xyz' % TEAM_A, None),
    # delete-configurations(B site + A team 组合,无配置所以无破坏)
    ('del-cfg Bsite+A   ', 'DELETE', '/.netlify/functions/delete-configurations-for-site?teamId=%s&siteId=%s' % (TEAM_A, SITE_B), None),
    # manage-extension-proxy 交叉
    ('manage-ext B team ', 'GET', '/.netlify/functions/manage-extension-proxy?teamId=%s' % TEAM_B, None),
]
for label, method, path, body in cases:
    st, out = fn(method, path, body)
    print('%-20s [%d] %s' % (label, st, out[:250]))
