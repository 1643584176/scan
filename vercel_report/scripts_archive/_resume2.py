# -*- coding: utf-8 -*-
import sys, json
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

for ep in ['/v2/sandboxes/v48/resume?teamId=%s&projectId=%s' % (TEAM, PROJ),
           '/v2/sandboxes/v48/start?teamId=%s&projectId=%s' % (TEAM, PROJ),
           '/v2/sandboxes/resume?teamId=%s&projectId=%s' % (TEAM, PROJ)]:
    c, r = api('POST', ep, {}, timeout=90)
    print(ep.split('?')[0], '->', c, r[:400])
    if c == 200:
        break
