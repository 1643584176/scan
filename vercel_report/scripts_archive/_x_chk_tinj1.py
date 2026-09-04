# -*- coding: utf-8 -*-
"""检查 tinj1 sandbox 是否存在 (MMDS 重测依赖)"""
import sys, json
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ
c, r = api('GET', '/v2/sandboxes/tinj1?teamId=%s&projectId=%s' % (TEAM, PROJ))
print('status:', c)
print((r or '')[:400])
