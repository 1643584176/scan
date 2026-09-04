# -*- coding: utf-8 -*-
"""清理全部 stopped sandbox, 释放并发配额"""
import sys, json, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

c, r = api('GET', '/v2/sandboxes?teamId=%s&project=%s&limit=50' % (TEAM, PROJ))
print('status:', c)
if c != 200:
    print(r[:300])
    sys.exit(0)
d = json.loads(r)
kept = []
for s in d.get('sandboxes', []):
    st = s.get('status')
    if st == 'running':
        kept.append(s.get('name'))
        continue
    nm = s.get('name')
    if not nm:
        nm = s.get('id')
    c2, r2 = api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (nm, TEAM, PROJ))
    print('del %s (%s) -> %s' % (nm, st, c2))
    time.sleep(0.5)
print('kept running:', kept)
