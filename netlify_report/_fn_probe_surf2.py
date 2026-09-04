# -*- coding: utf-8 -*-
"""Netlify:细测 agent-runner-file-delete + delete-configurations-for-site 结构"""
import http.client, ssl, gzip, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A
ctx = ssl.create_default_context()

def req(path, method='POST', body=None, qs=''):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=20)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept': 'application/json', 'Cookie': COOKIE_A,
         'Origin': 'https://app.netlify.com', 'Referer': 'https://app.netlify.com/'}
    if body is not None:
        h['Content-Type'] = 'application/json'
        body = json.dumps(body).encode()
    try:
        conn.request(method, path + qs, body=body, headers=h)
        r = conn.getresponse(); raw = r.read()
        enc = r.getheader('Content-Encoding')
        if enc == 'gzip': raw = gzip.decompress(raw)
        st = r.status; conn.close()
        return st, raw[:300].decode('utf-8', 'replace')
    except Exception as e:
        return -1, 'ERR %s' % str(e)[:60]

P = '/.netlify/functions/agent-runner-file-delete'
A_TEAM_SLUG = '1643584176'
A_TEAM_UUID = '6a979dd2ae93f47d55b62897'
print('=== agent-runner-file-delete:accountId 形态 ===')
for acc in [A_TEAM_SLUG, A_TEAM_UUID, 'nonexistent-team-xyz', '00000000-0000-0000-0000-000000000000', '']:
    s, b = req(P, body={'accountId': acc, 'fileKey': 'x'})
    print('accountId=%-42r -> %d %s' % (acc, s, b[:180].replace('\n', ' ')))

print()
print('=== fileKey 形态(accountId=A slug)===')
for fk in ['x', 'a.txt', 'dir/a.txt', 'a/b/c.json', '00000000-0000-0000-0000-000000000000',
           'agent-6a98d5e6448c07a76d7babf3', '../x', '/etc/passwd', 'x/y']:
    s, b = req(P, body={'accountId': A_TEAM_SLUG, 'fileKey': fk})
    print('fileKey=%-42r -> %d %s' % (fk, s, b[:180].replace('\n', ' ')))

print()
print('=== delete-configurations-for-site ===')
P2 = '/.netlify/functions/delete-configurations-for-site'
for method, qs, body in [('DELETE', '', None), ('DELETE', '?siteId=%s' % '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4', None),
                         ('POST', '', {'siteId': '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'}),
                         ('GET', '', None)]:
    s, b = req(P2, method=method, body=body, qs=qs)
    print('%s %s body=%s -> %d %s' % (method, qs[:60], json.dumps(body)[:60] if body else '-', s, b[:180].replace('\n', ' ')))
