# -*- coding: utf-8 -*-
"""t2: JSON 解析差异(带 Origin 头认证)
POST /api/tagged_file — 探测 file_tags 合法值 + 解析差异向量
"""
import json, sys, http.client, ssl, gzip, brotli
sys.path.insert(0, 'D:/scan/figma_report')
from _figma_creds import COOKIE_B, TEAM_A, TEAM_B

HOST = 'www.figma.com'
ORIGIN = 'https://www.figma.com'

def req(method, path, body=None, ct='application/json', cookie=COOKIE_B, extra=None):
    ctx = ssl.create_default_context()
    conn = http.client.HTTPSConnection(HOST, context=ctx, timeout=20)
    hdrs = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
            'Accept-Encoding': 'br, gzip', 'Origin': ORIGIN, 'Referer': ORIGIN + '/'}
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

print('=== 1. file_tags 值探测(找合法值) ===')
for tag in [['review'], ['starter_files'], ['all'], [], ['starred'], ['needs_review'], 'starter_files', [1], ['review','x']]:
    body = {'file_tags': tag, 'current_org_id': None, 'current_team_id': TEAM_B, 'should_recreate': False}
    s, txt = req('POST', '/api/tagged_file', body)
    print('[%r] %d %s' % (tag, s, txt[:220].replace('\n', ' ')))

print()
print('=== 2. 解析差异向量 ===')
cases = [
    ('CT=form+JSON', 'application/x-www-form-urlencoded',
     {'file_tags': ['review'], 'current_org_id': None, 'current_team_id': TEAM_A, 'should_recreate': False}),
    ('CT=text/plain', 'text/plain',
     {'file_tags': ['review'], 'current_org_id': None, 'current_team_id': TEAM_A, 'should_recreate': False}),
    ('精度:浮点teamId', 'application/json',
     {'file_tags': ['review'], 'current_org_id': None, 'current_team_id': 1.6663827066634622e18, 'should_recreate': False}),
    ('teamId=字符串A', 'application/json',
     {'file_tags': ['review'], 'current_org_id': None, 'current_team_id': TEAM_A, 'should_recreate': False}),
    ('重复键teamId B/A', 'application/json',
     '{"file_tags":["review"],"current_org_id":null,"current_team_id":"%s","current_team_id":"%s","should_recreate":false}' % (TEAM_B, TEAM_A)),
    ('重复键file_tags 空/有效', 'application/json',
     '{"file_tags":[],"file_tags":["review"],"current_org_id":null,"current_team_id":"%s","should_recreate":false}' % TEAM_B),
    ('null current_team_id', 'application/json',
     {'file_tags': ['review'], 'current_org_id': None, 'current_team_id': None, 'should_recreate': False}),
    ('字符串current_team_id=数字', 'application/json',
     {'file_tags': ['review'], 'current_org_id': None, 'current_team_id': '1667396394890946753.0', 'should_recreate': False}),
]
for label, ct, body in cases:
    s, txt = req('POST', '/api/tagged_file', body, ct=ct)
    print('[%s] %d %s' % (label, s, txt[:220].replace('\n', ' ')))
