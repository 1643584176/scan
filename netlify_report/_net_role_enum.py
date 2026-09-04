# -*- coding: utf-8 -*-
"""枚举 POST members 有效 role 值(用 B email)"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A

ctx = ssl.create_default_context()

def req(method, path, body=None, token=TOKEN_A, timeout=25):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json'}
    if token: h['Authorization'] = 'Bearer ' + token
    b = json.dumps(body).encode() if body is not None else None
    conn.request(method, path, body=b, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br': raw = brotli.decompress(raw)
    elif enc == 'gzip': raw = gzip.decompress(raw)
    st = r.status
    txt = raw.decode('utf-8', 'ignore')
    conn.close()
    return st, txt

roles = ['Developer', 'Admin', 'Reviewer', 'Guest', 'Contributor', 'Member',
         'developer', 'admin', 'reviewer', 'guest', 'Owner', 'Dev', 'Collaborator']
for r in roles:
    st, b = req('POST', '/api/v1/1643584176/members',
                {'email': '729488839@qq.com', 'role': r})
    mark = ''
    if st in (200, 201, 202):
        mark = '  <<< SUCCESS'
        print('role=%-12s %s | %s%s' % (r, st, b[:300].replace('\n', ' '), mark))
        # 成功后撤销邀请: 从响应拿 invite/member id
        try:
            d = json.loads(b)
            mid = d.get('id') or d.get('invite_id')
            if mid:
                req('DELETE', '/api/v1/1643584176/members/%s' % mid)
                print('    -> cleaned member', mid)
        except Exception:
            pass
        break
    print('role=%-12s %s | %s' % (r, st, b[:160].replace('\n', ' ')))
