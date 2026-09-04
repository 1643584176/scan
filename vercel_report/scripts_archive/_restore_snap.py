# -*- coding: utf-8 -*-
import sys, json
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

SNAP = 'snap_QVjWeSAP581ZZzjrdwiQyAizoyXe'
c, r = api('GET', '/v2/snapshots/%s?teamId=%s' % (SNAP, TEAM))
print('get snap:', c, r[:800])

# 尝试 restore 端点
for ep in ['/v2/snapshots/%s/restore?teamId=%s&project=%s' % (SNAP, TEAM, PROJ),
           '/v2/snapshots/%s/restore?teamId=%s' % (SNAP, TEAM),
           '/v2/sandboxes/snapshots/%s/restore?teamId=%s&project=%s' % (SNAP, TEAM, PROJ)]:
    c, r = api('POST', ep, {})
    print('restore', ep, '->', c, r[:300])
