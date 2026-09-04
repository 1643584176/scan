# -*- coding: utf-8 -*-
"""环境检查: token 有效性 + sandbox 列表"""
import sys, json
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

c, r = api('GET', '/v2/sandboxes?teamId=%s&project=%s&limit=50' % (TEAM, PROJ))
print('status:', c)
if c == 200:
    d = json.loads(r)
    for s in d.get('sandboxes', []):
        print(s.get('name'), '|', s.get('id'), '|', s.get('currentSessionId'), '|', s.get('status'))
else:
    print(r[:500])
