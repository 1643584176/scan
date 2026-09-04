# -*- coding: utf-8 -*-
"""验证 token 对 /v2/user 与 team scope 接口的可用性"""
import json, urllib.request, urllib.error

tok = open(r'F:\scan\vercel_cookies.txt', encoding='utf-8').read().strip()
for ln in tok.splitlines():
    if ln.startswith('authorization=Bearer '):
        TOKEN = ln.split('Bearer ')[1].strip()
        break

BASE = 'https://api.vercel.com'

def api(path):
    req = urllib.request.Request(BASE + path, method='GET')
    req.add_header('Authorization', 'Bearer ' + TOKEN)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode()[:600]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:600]

for p in ['/v2/user',
          '/v2/sandboxes?teamId=team_GIy1SZ444lspqeNbh4r8uAUg&projectId=prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F&limit=1',
          '/v2/teams']:
    c, r = api(p)
    print('=== %s -> %d' % (p.split('?')[0], c))
    print(r[:500])
    print()
