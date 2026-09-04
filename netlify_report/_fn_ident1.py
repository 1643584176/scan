# -*- coding: utf-8 -*-
"""Netlify:identeer-proxy 子路径探测(providers/connections)"""
import http.client, ssl, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, COOKIE_B
ctx = ssl.create_default_context()

def req(path, cookie=COOKIE_A):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=20)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept': 'application/json', 'Cookie': cookie, 'Origin': 'https://app.netlify.com'}
    conn.request('GET', path, headers=h)
    r = conn.getresponse(); raw = r.read()
    st = r.status; conn.close()
    return st, raw[:600].decode('utf-8', 'replace')

BASE = '/.netlify/functions/identeer-proxy'
paths = ['/providers', '/connections', '/connections/github', '/connections/github_integration_provider',
         '/connections/netlify_integration_provider', '/connections/slack_integration_provider',
         '/disconnect/github_integration_provider', '/health', '']
for p in paths:
    s, b = req(BASE + p, COOKIE_A)
    print('A GET %-55s -> %d %s' % (p or '/', s, b[:280].replace('\n', ' ')))
print()
for p in ['/providers']:
    s, b = req(BASE + p, COOKIE_B)
    print('B GET %-55s -> %d %s' % (p, s, b[:280].replace('\n', ' ')))
