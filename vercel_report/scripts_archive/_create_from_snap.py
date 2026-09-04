# -*- coding: utf-8 -*-
import sys, json
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

api('DELETE', '/v2/sandboxes/v50r?teamId=%s&projectId=%s' % (TEAM, PROJ))
body = {"projectId": PROJ, "name": "v50r",
        "source": {"type": "snapshot", "snapshotId": "snap_QVjWeSAP581ZZzjrdwiQyAizoyXe"}}
c, r = api('POST', '/v2/sandboxes?teamId=%s' % TEAM, body, timeout=120)
print(c, r[:800])
