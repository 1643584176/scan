# -*- coding: utf-8 -*-
"""CSRF 面检查:
1. Origin 值是否校验(evil.com / null / 空)
2. Set-Cookie 的 SameSite 属性
3. 响应 CORS 头
"""
import json, sys, http.client, ssl, gzip, brotli
sys.path.insert(0, 'D:/scan/figma_report')
from _figma_creds import COOKIE_B, TEAM_B

HOST = 'www.figma.com'
BODY = {'file_tags': ['review'], 'current_org_id': None, 'current_team_id': TEAM_B, 'should_recreate': False}

def req(origin=None, referer=None, want_headers=True):
    ctx = ssl.create_default_context()
    conn = http.client.HTTPSConnection(HOST, context=ctx, timeout=20)
    hdrs = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip',
            'Cookie': COOKIE_B, 'Content-Type': 'application/json'}
    if origin is not None:
        hdrs['Origin'] = origin
    if referer is not None:
        hdrs['Referer'] = referer
    body = json.dumps(BODY)
    hdrs['Content-Length'] = str(len(body))
    conn.request('POST', '/api/tagged_file', body=body, headers=hdrs)
    resp = conn.getresponse()
    h = {k.lower(): v for k, v in resp.getheaders()}
    raw = resp.read()
    enc = resp.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    conn.close()
    txt = raw.decode('utf-8', 'ignore')
    cors = {k: v for k, v in h.items() if 'access-control' in k}
    sc = {k: v for k, v in h.items() if k == 'set-cookie'}
    return resp.status, txt[:150].replace('\n', ' '), cors, sc

print('=== Origin 值校验 ===')
for label, o, r in [
    ('正常 Origin', 'https://www.figma.com', 'https://www.figma.com/'),
    ('evil Origin', 'https://evil.com', 'https://evil.com/'),
    ('null Origin', 'null', None),
    ('空串 Origin', '', None),
    ('无 Origin 无 Referer', None, None),
    ('evil Referer only', None, 'https://evil.com/x'),
]:
    s, txt, cors, sc = req(o, r)
    print('[%s] %d %s CORS=%s' % (label, s, txt, cors))

print()
print('=== 登录后页面 Set-Cookie SameSite 属性 ===')
ctx = ssl.create_default_context()
conn = http.client.HTTPSConnection(HOST, context=ctx, timeout=20)
conn.request('GET', '/', headers={'User-Agent': 'Mozilla/5.0', 'Cookie': COOKIE_B})
resp = conn.getresponse()
resp.read()
for k, v in resp.getheaders():
    if k.lower() == 'set-cookie':
        print('  Set-Cookie:', v[:200])
conn.close()
