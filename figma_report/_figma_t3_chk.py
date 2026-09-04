# -*- coding: utf-8 -*-
"""确认 FILE_B 是否被 team_id/creator_id 修改 + 恢复"""
import json, sys, http.client, ssl, gzip, brotli
sys.path.insert(0, 'D:/scan/figma_report')
from _figma_creds import COOKIE_B, FILE_B, TEAM_B

HOST = 'www.figma.com'
ORIGIN = 'https://www.figma.com'

def req(method, path, body=None, cookie=COOKIE_B):
    ctx = ssl.create_default_context()
    conn = http.client.HTTPSConnection(HOST, context=ctx, timeout=20)
    hdrs = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip',
            'Origin': ORIGIN, 'Referer': ORIGIN + '/'}
    if cookie:
        hdrs['Cookie'] = cookie
    if body is not None:
        hdrs['Content-Type'] = 'application/json'
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

# 当前状态
s, txt = req('GET', '/api/files/%s' % FILE_B)
print('GET FILE_B:', s)
try:
    meta = json.loads(txt)['meta']
    print('  key=%s name=%s team_id=%s folder_id=%s creator=%s' % (
        meta.get('key'), meta.get('name'), meta.get('team_id'),
        meta.get('folder_id'), meta.get('creator_id')))
except Exception as e:
    print('  parse err', e, txt[:200])

# 恢复:改名回去 + team 复原
s, txt = req('PUT', '/api/files/%s' % FILE_B, {'name': 'Untitled'})
print('恢复 name:', s, txt[:150].replace('\n', ' '))
