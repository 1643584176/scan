# -*- coding: utf-8 -*-
"""t3: PUT /api/files/{key} 字段接受度 + FILE_A 越权对比
对 FILE_B(自己)探测接受字段;对 FILE_A(只读)测相同字段
"""
import json, sys, http.client, ssl, gzip, brotli
sys.path.insert(0, 'D:/scan/figma_report')
from _figma_creds import COOKIE_B, FILE_A, FILE_B, TEAM_A, UID_A

HOST = 'www.figma.com'
ORIGIN = 'https://www.figma.com'

def req(method, path, body=None, ct='application/json', cookie=COOKIE_B):
    ctx = ssl.create_default_context()
    conn = http.client.HTTPSConnection(HOST, context=ctx, timeout=20)
    hdrs = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip',
            'Origin': ORIGIN, 'Referer': ORIGIN + '/'}
    if cookie:
        hdrs['Cookie'] = cookie
    if body is not None:
        hdrs['Content-Type'] = ct
        if isinstance(body, (dict, list)):
            body = json.dumps(body)
        hdrs['Content-Length'] = str(len(body))
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

fields = [
    ('proto_link_access=edit', {'proto_link_access': 'edit'}),
    ('org_audience=true', {'org_audience': True}),
    ('org_browsable=true', {'org_browsable': True}),
    ('has_file_link_password=false', {'has_file_link_password': False}),
    ('description', {'description': 't3desc'}),
    ('folder_id=A的draft文件夹', {'folder_id': '634606970'}),
    ('team_id=TEAM_A', {'team_id': TEAM_A}),
    ('creator_id=UID_A', {'creator_id': UID_A}),
    ('嵌套name+link_access', {'name': 'n', 'link_access': 'edit'}),
]

print('=== 对 FILE_B(自己) ===')
for label, body in fields:
    s, txt = req('PUT', '/api/files/%s' % FILE_B, body)
    print('[%s] %d %s' % (label, s, txt[:180].replace('\n', ' ')))

print()
print('=== 对 FILE_A(只读) ===')
for label, body in fields:
    s, txt = req('PUT', '/api/files/%s' % FILE_A, body)
    print('[%s] %d %s' % (label, s, txt[:180].replace('\n', ' ')))
