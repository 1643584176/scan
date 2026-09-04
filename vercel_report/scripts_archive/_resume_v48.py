# -*- coding: utf-8 -*-
import sys, json
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

c, r = api('GET', '/v2/sandboxes?teamId=%s&project=%s&limit=50' % (TEAM, PROJ))
print('list:', c)
d = json.loads(r)
for s in d.get('sandboxes', []):
    print(s['name'], s['status'], s.get('currentSnapshotId'))

# 尝试 stop/start v48 恢复
c, r = api('POST', '/v2/sandboxes/v48/stop?teamId=%s&projectId=%s' % (TEAM, PROJ))
print('stop v48:', c, r[:300])
c, r = api('POST', '/v2/sandboxes/v48/start?teamId=%s&projectId=%s' % (TEAM, PROJ))
print('start v48:', c, r[:300])
