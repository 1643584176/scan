# -*- coding: utf-8 -*-
"""t4 相关:上传/创建面探测
1. POST /api/files/create — body 结构
2. POST /file/{key}/image/batch — 图片导入
3. POST /api/design_systems/libraries_by_library_keys — 批量库查询(body 是 JSON)
"""
import json, sys, http.client, ssl, gzip, brotli
sys.path.insert(0, 'D:/scan/figma_report')
from _figma_creds import COOKIE_B, FILE_B, TEAM_A, TEAM_B

HOST = 'www.figma.com'
ORIGIN = 'https://www.figma.com'

def req(method, path, body=None, ct='application/json', cookie=COOKIE_B, raw_body=None):
    ctx = ssl.create_default_context()
    conn = http.client.HTTPSConnection(HOST, context=ctx, timeout=20)
    hdrs = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip',
            'Origin': ORIGIN, 'Referer': ORIGIN + '/'}
    if cookie:
        hdrs['Cookie'] = cookie
    b = raw_body
    if b is None and body is not None:
        if ct == 'multipart/form-data':
            b = body  # 已经是构造好的 multipart 串
        else:
            b = json.dumps(body)
    if b is not None:
        hdrs['Content-Type'] = ct
        hdrs['Content-Length'] = str(len(b))
    conn.request(method, path, body=b, headers=hdrs)
    resp = conn.getresponse()
    raw = resp.read()
    enc = resp.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    conn.close()
    return resp.status, raw.decode('utf-8', 'ignore')

print('=== POST /api/files/create ===')
for label, body in [
    ('空body', None),
    ('{}', {}),
    ('name', {'name': 't4create'}),
    ('name+team_id=TEAM_B', {'name': 't4b', 'team_id': TEAM_B}),
    ('name+team_id=TEAM_A', {'name': 't4a', 'team_id': TEAM_A}),
]:
    s, txt = req('POST', '/api/files/create', body)
    print('[%s] %d %s' % (label, s, txt[:220].replace('\n', ' ')))

print()
print('=== POST /file/FILE_B/image/batch ===')
for label, body, ct in [
    ('空body JSON', None, 'application/json'),
    ('{}', {}, 'application/json'),
    ('multipart畸形', '----------------------------x\r\nContent-Disposition: form-data; name="file"; filename="a.png"\r\nContent-Type: image/png\r\n\r\nPNGDATA\r\n----------------------------x--\r\n', 'multipart/form-data; boundary=--------------------------x'),
]:
    s, txt = req('POST', '/file/%s/image/batch' % FILE_B, body, ct=ct)
    print('[%s] %d %s' % (label, s, txt[:220].replace('\n', ' ')))

print()
print('=== POST /api/design_systems/libraries_by_library_keys ===')
for label, body in [
    ('A文件key', {'library_keys': ['lk-5a31d104cabc6a74d4edf6425e7bc6575e9c0f18cda7efb746193aef4d915b077d115c985e6cf49d36d97d']}),
    ('B文件key', {'library_keys': [FILE_B]}),
]:
    s, txt = req('POST', '/api/design_systems/libraries_by_library_keys', body)
    print('[%s] %d %s' % (label, s, txt[:220].replace('\n', ' ')))
