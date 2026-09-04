# -*- coding: utf-8 -*-
"""identeer-proxy 集成账号端点交叉 + fetch-site-configuration + agent-file-delete
1. identeer /providers 列表拿 provider id
2. integrations/accounts/{acc}/integration-provider/{pid}:自队/交叉
3. fetch-site-configuration(siteId/teamId/integrationSlug)交叉
4. agent-runner-file-delete:POST 不存在 fileKey(无破坏)交叉
"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, SITE_A

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
TEAM_A = '6a979dd2ae93f47d55b62897'
TEAM_B = '6a97b6454fef0db964f75db6'
ctx = ssl.create_default_context()
BASE = '/.netlify/functions/identeer-proxy'


def fn(method, path, body=None, cookie=COOKIE_A):
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
    out = raw[:500].decode('utf-8', 'ignore')
    conn.close()
    return st, out


print('== providers 结构 ==')
st, out = fn('GET', BASE + '/providers')
print('[%d] %s' % (st, out[:400]))
print()

print('== identeer 集成账号端点 ==')
for label, path in [
    ('self acc, no pid ', '%s/integrations/accounts/%s/integration-provider/' % (BASE, TEAM_A)),
    ('self acc, xyz pid', '%s/integrations/accounts/%s/integration-provider/xyz' % (BASE, TEAM_A)),
    ('cross acc (B)    ', '%s/integrations/accounts/%s/integration-provider/xyz' % (BASE, TEAM_B)),
    ('no acc           ', '%s/integrations/accounts//integration-provider/xyz' % (BASE,)),
    ('bad acc uuid     ', '%s/integrations/accounts/00000000-0000-0000-0000-000000000000/integration-provider/xyz' % (BASE,)),
]:
    st, out = fn('GET', path)
    print('%-20s [%d] %s' % (label, st, out[:250]))
print()

print('== fetch-site-configuration ==')
for label, q in [
    ('self site, no slug ', '?siteId=%s&teamId=%s' % (SITE_A, TEAM_A)),
    ('self site, x slug  ', '?siteId=%s&teamId=%s&integrationSlug=xyz' % (SITE_A, TEAM_A)),
    ('B site + A team    ', '?siteId=%s&teamId=%s&integrationSlug=xyz' % (SITE_B, TEAM_A)),
    ('A site + B team    ', '?siteId=%s&teamId=%s&integrationSlug=xyz' % (SITE_A, TEAM_B)),
]:
    st, out = fn('GET', '/.netlify/functions/fetch-site-configuration' + q)
    print('%-20s [%d] %s' % (label, st, out[:250]))
print()

print('== agent-runner-file-delete(不存在 fileKey,无破坏) ==')
for label, q in [
    ('self acc, no key   ', '?accountId=%s' % TEAM_A),
    ('self acc, fake key ', '?accountId=%s&fileKey=00000000-0000-0000-0000-000000000000' % TEAM_A),
    ('cross acc (B)      ', '?accountId=%s&fileKey=00000000-0000-0000-0000-000000000000' % TEAM_B),
]:
    st, out = fn('POST', '/.netlify/functions/agent-runner-file-delete' + q)
    print('%-20s [%d] %s' % (label, st, out[:250]))
