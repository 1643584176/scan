# -*- coding: utf-8 -*-
"""knowledge scopes 变体确认(A cookie 试各种 B 的 scope)"""
import http.client, ssl, gzip, brotli, json, sys, urllib.parse
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
TEAM_B = '6a97b6454fef0db964f75db6'
ctx = ssl.create_default_context()


def spark(path, cookie=COOKIE_A):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=25)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json', 'Cookie': cookie}
    conn.request('GET', path, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    out = raw[:200].decode('utf-8', 'ignore')
    conn.close()
    return st, out


def sc(s):
    return urllib.parse.quote(json.dumps(s))


cases = [
    ('B siteId      ', {'siteId': SITE_B}),
    ('B accountId   ', {'accountId': TEAM_B}),
    ('B site+acct   ', {'siteId': SITE_B, 'accountId': TEAM_B}),
    ('A site+B acct ', {'siteId': '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4', 'accountId': TEAM_B}),
    ('B teamId 猜   ', {'teamId': TEAM_B}),
    ('B site+teamId ', {'siteId': SITE_B, 'teamId': TEAM_B}),
    ('siteId 数组   ', {'siteId': [SITE_B]}),
    ('siteId 对象   ', {'siteId': {'eq': SITE_B}}),
]
for label, s in cases:
    st, out = spark('/spark-proxy/api/v1/knowledge/?scopes=%s' % sc(s))
    print('%-14s [%d] %s' % (label, st, out[:150]))
