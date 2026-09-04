# -*- coding: utf-8 -*-
import sys, json
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

c, r = api('GET', '/v2/sandboxes/v48?teamId=%s&projectId=%s&resume=true' % (TEAM, PROJ), timeout=120)
print('resume v48:', c, r[:600])
