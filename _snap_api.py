# -*- coding: utf-8 -*-
"""探索快照管理 API 端点"""
import sys, json, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
from vercel_driver import api, TEAM, PROJ

# 候选端点
cands = [
    ('GET', '/v2/snapshots?teamId=%s' % TEAM),
    ('GET', '/v2/sandboxes/snapshots?teamId=%s' % TEAM),
    ('GET', '/v2/sandboxes/snapshots?teamId=%s&project=%s' % (TEAM, PROJ)),
    ('GET', '/v1/snapshots?teamId=%s' % TEAM),
    ('GET', '/v2/sandboxes?teamId=%s&project=%s&includeSnapshots=true' % (TEAM, PROJ)),
    ('GET', '/v2/sandboxes/snapshots?project=%s' % PROJ),
    ('GET', '/v2/snapshots?projectId=%s' % PROJ),
]
for m, p in cands:
    c, r = api(m, p)
    print('%s %s -> %d %s' % (m, p.split('?')[0][:40], c, r[:200].replace('\n', ' ')))
    time.sleep(0.3)

# 试 openapi
c, r = api('GET', '/docs/openapi.json')
print('openapi:', c, r[:200])
