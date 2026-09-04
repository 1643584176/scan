# -*- coding: utf-8 -*-
"""查询/恢复 scanl4 沙箱: GET 详情 + 尝试 resume"""
import sys, json
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api

TEAM = 'team_GIy1SZ444lspqeNbh4r8uAUg'
PROJ = 'prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F'

# 1) GET 详情
c, r = api('GET', '/v2/sandboxes/scanl4?teamId=%s&projectId=%s' % (TEAM, PROJ))
print('GET scanl4:', c)
print(r[:2000])

# 2) 尝试 resume (多个候选端点)
for ep in ['/v2/sandboxes/scanl4/resume',
           '/v2/sandboxes/scanl4/start',
           '/v2/sandboxes/scanl4/sessions']:
    c, r = api('POST', ep + '?teamId=%s&projectId=%s' % (TEAM, PROJ), {})
    print('POST %s -> %d %s' % (ep, c, r[:300]))
