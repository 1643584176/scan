# -*- coding: utf-8 -*-
"""查看快照当前数量"""
import sys, json
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
from vercel_driver import api, TEAM, PROJ

c, r = api('GET', '/v2/sandboxes/snapshots?teamId=%s&project=%s&limit=50' % (TEAM, PROJ))
if c == 200:
    snaps = json.loads(r).get('snapshots', [])
    print('remaining snapshots:', len(snaps))
    for s in snaps[:5]:
        print(' ', s['id'], s.get('sizeBytes', 0), s.get('status'))
else:
    print(c, r[:300])
