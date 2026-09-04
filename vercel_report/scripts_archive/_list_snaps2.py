# -*- coding: utf-8 -*-
import sys, json, time
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

c, r = api('GET', '/v2/sandboxes/snapshots?teamId=%s&project=%s&limit=50' % (TEAM, PROJ), timeout=30)
print('snaps:', c)
d = json.loads(r)
for s in d.get('snapshots', []):
    t = time.strftime('%m-%d %H:%M:%S', time.localtime(s['createdAt'] / 1000))
    print(s['id'], s['status'], s['sourceSessionId'], t, s.get('sizeBytes'))
