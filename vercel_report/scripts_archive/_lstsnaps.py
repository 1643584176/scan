# -*- coding: utf-8 -*-
import json, sys
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ
c, r = api("GET", "/v2/sandboxes/snapshots?teamId=%s&project=%s&limit=100" % (TEAM, PROJ))
print('status:', c)
print('body:', (r or '')[:800])
if c == 200:
    snaps = json.loads(r).get('snapshots', [])
    print('snapshots:', len(snaps))
    for s in snaps[:20]:
        print(' ', s.get('id'), s.get('status'), s.get('createdAt', '')[:19], s.get('sizeBytes'))
