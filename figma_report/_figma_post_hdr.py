# -*- coding: utf-8 -*-
"""确认 POST 认证需要的头"""
import json, sys, http.client, ssl, gzip, brotli
sys.path.insert(0, 'D:/scan/figma_report')
from _figma_creds import COOKIE_B, TEAM_B, UID_B

HOST = 'www.figma.com'
BODY = {'file_tags': ['review'], 'current_org_id': None, 'current_team_id': TEAM_B, 'should_recreate': False}

def req(extra=None):
    ctx = ssl.create_default_context()
    conn = http.client.HTTPSConnection(HOST, context=ctx, timeout=20)
    hdrs = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip',
            'Cookie': COOKIE_B, 'Content-Type': 'application/json'}
    if extra:
        hdrs.update(extra)
    body = json.dumps(BODY)
    hdrs['Content-Length'] = str(len(body))
    conn.request('POST', '/api/tagged_file', body=body, headers=hdrs)
    resp = conn.getresponse()
    raw = resp.read()
    enc = resp.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    conn.close()
    return resp.status, raw.decode('utf-8', 'ignore')

cases = [
    ('无额外头', {}),
    ('仅Origin', {'Origin': 'https://www.figma.com'}),
    ('仅Referer', {'Referer': 'https://www.figma.com/'}),
    ('仅X-Figma-User-Id', {'X-Figma-User-Id': UID_B}),
    ('Origin+Referer', {'Origin': 'https://www.figma.com', 'Referer': 'https://www.figma.com/'}),
]
for label, extra in cases:
    s, txt = req(extra)
    print('[%s] %d %s' % (label, s, txt[:160].replace('\n', ' ')))
