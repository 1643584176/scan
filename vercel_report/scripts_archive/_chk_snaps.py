# -*- coding: utf-8 -*-
"""枚举快照列表/删除 API, 定位占用存储配额的快照 (配额 402: Hobby Snapshots Storage)"""
import sys, json, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

# 1. 确认 sdk46b 是否已删
c, r = api('GET', '/v2/sandboxes?teamId=%s&project=%s&limit=50' % (TEAM, PROJ))
print('list sandboxes:', c, (r or '')[:400])
print()

# 2. 枚举快照列表端点
cands = [
    ('GET', '/v2/snapshots?teamId=%s&projectId=%s' % (TEAM, PROJ)),
    ('GET', '/v2/snapshots?teamId=%s&project=%s&limit=20' % (TEAM, PROJ)),
    ('GET', '/v2/sandboxes/snapshots?teamId=%s&project=%s&limit=20' % (TEAM, PROJ)),
    ('GET', '/v1/snapshots?teamId=%s' % TEAM),
    ('GET', '/v4/snapshots?teamId=%s' % TEAM),
    ('GET', '/v2/sandboxes/snapshots?teamId=%s&limit=20' % (TEAM)),
]
for m, p in cands:
    c, r = api(m, p, timeout=30)
    print('%s %s -> %d %s' % (m, p, c, (r or '')[:300]), flush=True)
    time.sleep(1)
