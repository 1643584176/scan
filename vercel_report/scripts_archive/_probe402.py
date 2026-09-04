# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
from vercel_driver import api, TEAM, PROJ
c, r = api('POST', '/v4/sandboxes?teamId=%s' % TEAM, {'projectId': PROJ, 'name': 'v38probe'}, 30)
print('status:', c)
print('body:', (r or '')[:600])
