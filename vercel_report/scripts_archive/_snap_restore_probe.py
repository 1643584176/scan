# -*- coding: utf-8 -*-
import sys, json
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

for key in ['snapshotId', 'snapshot', 'sourceSnapshot', 'restoreFrom', 'resumeFrom', 'fromSnapshot']:
    body = {"name": "v48r2", key: "snap_EfNKGWYRKcRn2CWPuchZ0lAw5Uuk"}
    c, r = api('POST', '/v4/sandboxes?teamId=%s&project=%s' % (TEAM, PROJ), body, timeout=60)
    print(key, '->', c, r[:200])
    if c == 200:
        print('SUCCESS with', key)
        break
