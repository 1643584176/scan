# -*- coding: utf-8 -*-
"""拿 A/B 已装扩展(真实 slug),identeer 真实 provider id 结构
1. fetch-installed-extensions-for-team?teamId=X(cookie A/B 各自)
2. identeer: 自队 provider id 1..6
"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, COOKIE_B, SITE_A

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
TEAM_A = '6a979dd2ae93f47d55b62897'
TEAM_B = '6a97b6454fef0db964f75db6'
ctx = ssl.create_default_context()


def fn(method, path, body=None, cookie=COOKIE_A, rawlen=900):
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


print('== A team installed extensions ==')
st, out = fn('GET', '/.netlify/functions/fetch-installed-extensions-for-team?teamId=%s' % TEAM_A, cookie=COOKIE_A)
print('[%d] %s' % (st, out[:700]))
print()
print('== B team installed extensions ==')
st, out = fn('GET', '/.netlify/functions/fetch-installed-extensions-for-team?teamId=%s' % TEAM_B, cookie=COOKIE_B)
print('[%d] %s' % (st, out[:700]))
print()
print('== A relevant extensions for site A ==')
st, out = fn('GET', '/.netlify/functions/fetch-relevant-installed-extensions-for-site?siteId=%s&teamId=%s' % (SITE_A, TEAM_A), cookie=COOKIE_A)
print('[%d] %s' % (st, out[:700]))
print()
print('== B relevant extensions for site B ==')
st, out = fn('GET', '/.netlify/functions/fetch-relevant-installed-extensions-for-site?siteId=%s&teamId=%s' % (SITE_B, TEAM_B), cookie=COOKIE_B)
print('[%d] %s' % (st, out[:700]))
print()
print('== identeer self team provider 1..6 ==')
for pid in range(1, 7):
    st, out = fn('GET', '/.netlify/functions/identeer-proxy/integrations/accounts/%s/integration-provider/%d' % (TEAM_A, pid))
    print('pid=%d [%d] %s' % (pid, st, out[:250]))
