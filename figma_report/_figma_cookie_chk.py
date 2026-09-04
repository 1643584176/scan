# -*- coding: utf-8 -*-
"""验证 B cookie 在 REST 上是否有效:对比匿名/带cookie"""
import json, sys, http.client, ssl, gzip, brotli
sys.path.insert(0, 'D:/scan/figma_report')
from _figma_creds import COOKIE_B, UID_B, TEAM_B

HOST = 'www.figma.com'

def req(method, path, body=None, ct='application/json', cookie=None, extra=None):
    ctx = ssl.create_default_context()
    conn = http.client.HTTPSConnection(HOST, context=ctx, timeout=20)
    hdrs = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
            'Accept-Encoding': 'br, gzip'}
    if cookie:
        hdrs['Cookie'] = cookie
    if body is not None:
        hdrs['Content-Type'] = ct
        if isinstance(body, (dict, list)):
            body = json.dumps(body)
        hdrs['Content-Length'] = str(len(body))
    if extra:
        hdrs.update(extra)
    conn.request(method, path, body=body, headers=hdrs)
    resp = conn.getresponse()
    raw = resp.read()
    enc = resp.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    conn.close()
    return resp.status, raw.decode('utf-8', 'ignore')

for label, ck in [('无cookie', None), ('B cookie', COOKIE_B)]:
    s, txt = req('GET', '/api/authed_users/plans', cookie=ck)
    print('[%s] GET /api/authed_users/plans -> %d %s' % (label, s, txt[:200].replace('\n', ' ')))

s, txt = req('GET', '/api/user/%s/segments' % UID_B, cookie=COOKIE_B)
print('[B cookie] GET /api/user/B/segments -> %d %s' % (s, txt[:200].replace('\n', ' ')))

s, txt = req('GET', '/api/session/sync', cookie=COOKIE_B)
print('[B cookie] GET /api/session/sync -> %d %s' % (s, txt[:200].replace('\n', ' ')))

# 带额外头试 POST
s, txt = req('POST', '/api/tagged_file',
             {'fileTags': ['review'], 'currentOrgId': None, 'currentTeamId': TEAM_B, 'shouldRecreate': False},
             cookie=COOKIE_B, extra={'Origin': 'https://www.figma.com',
                                     'Referer': 'https://www.figma.com/',
                                     'X-Figma-User-Id': UID_B})
print('[B cookie+origin] POST /api/tagged_file -> %d %s' % (s, txt[:200].replace('\n', ' ')))
