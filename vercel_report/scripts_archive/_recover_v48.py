# -*- coding: utf-8 -*-
import sys, json
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

# 尝试 resume
for ep in ['/v2/sandboxes/v48/resume?teamId=%s&project=%s' % (TEAM, PROJ),
           '/v2/sandboxes/v48/resume?teamId=%s&projectId=%s' % (TEAM, PROJ),
           '/v2/sandboxes/v48?action=resume&teamId=%s&project=%s' % (TEAM, PROJ)]:
    c, r = api('POST', ep, {})
    print('resume:', c, r[:300])

# 从快照创建新沙箱
c, r = api('POST', '/v4/sandboxes?teamId=%s&project=%s' % (TEAM, PROJ),
           {"name": "v48r", "sourceSnapshotId": "snap_EfNKGWYRKcRn2CWPuchZ0lAw5Uuk"}, timeout=60)
print('create-from-snap:', c, r[:500])
