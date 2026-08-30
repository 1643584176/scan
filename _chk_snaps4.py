# -*- coding: utf-8 -*-
"""快照列表 400 调试"""
import sys
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

for qs in [
    '?teamId=%s&project=%s&limit=50' % (TEAM, PROJ),
    '?teamId=%s&projectId=%s&limit=50' % (TEAM, PROJ),
    '?teamId=%s&limit=50' % TEAM,
    '?teamId=%s&project=%s' % (TEAM, PROJ),
]:
    c, r = api('GET', '/v2/sandboxes/snapshots' + qs)
    print(qs, '->', c, (r or '')[:300], flush=True)
    print('---', flush=True)
