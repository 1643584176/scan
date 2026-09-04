# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

c, r = api('GET', '/v2/sandboxes?teamId=%s&project=%s&limit=50' % (TEAM, PROJ))
print('list:', c, (r or '')[:800])
print()
c, r = api('POST', '/v4/sandboxes?teamId=%s' % TEAM, {'projectId': PROJ, 'name': 'quota_probe_now'}, 30)
print('create:', c)
print('body:', (r or '')[:800])
