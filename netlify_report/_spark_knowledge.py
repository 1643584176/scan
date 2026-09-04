# -*- coding: utf-8 -*-
"""Spark knowledge API 探测:
1. A 自己 site(基线)
2. 交叉 scopes={siteId: B}(A cookie)
3. scopes 变体(空/只 accountId/畸形)
4. prompt-templates public/team"""
import http.client, ssl, gzip, brotli, json, sys, urllib.parse
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, COOKIE_B, SITE_A

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
TEAM_A = '6a979dd2ae93f47d55b62897'
TEAM_B = '6a97b6454fef0db964f75db6'
ctx = ssl.create_default_context()


def spark(method, path, body=None, cookie=COOKIE_A):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=30)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json', 'Cookie': cookie}
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
    out = raw[:1500].decode('utf-8', 'ignore')
    conn.close()
    return st, out


def sc(s):
    return urllib.parse.quote(json.dumps(s))


print('== knowledge 读取 ==')
st, out = spark('GET', '/spark-proxy/api/v1/knowledge/?scopes=%s' % sc({'siteId': SITE_A}))
print('A site(A cookie) [%d] %s' % (st, out[:300]))
st, out = spark('GET', '/spark-proxy/api/v1/knowledge/?scopes=%s' % sc({'siteId': SITE_B}))
print('B site(A cookie) [%d] %s' % (st, out[:500]))
st, out = spark('GET', '/spark-proxy/api/v1/knowledge/?scopes=%s' % sc({'siteId': SITE_B}), cookie=COOKIE_B)
print('B site(B cookie) [%d] %s' % (st, out[:500]))
st, out = spark('GET', '/spark-proxy/api/v1/knowledge/?scopes=%s' % sc({'siteId': SITE_A, 'accountId': TEAM_A}))
print('A site+acct      [%d] %s' % (st, out[:300]))
st, out = spark('GET', '/spark-proxy/api/v1/knowledge/?scopes=%s' % sc({}))
print('empty scopes     [%d] %s' % (st, out[:300]))
st, out = spark('GET', '/spark-proxy/api/v1/knowledge/')
print('no scopes        [%d] %s' % (st, out[:300]))
print()

print('== prompt-templates ==')
st, out = spark('GET', '/spark-proxy/api/prompt-templates/public?page=1&pageSize=5')
print('public list      [%d] %s' % (st, out[:600]))
st, out = spark('GET', '/spark-proxy/api/prompt-templates/team/xxx')
print('team xxx         [%d] %s' % (st, out[:300]))
