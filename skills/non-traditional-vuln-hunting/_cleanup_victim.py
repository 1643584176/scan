# -*- coding: utf-8 -*-
"""清理 victim 测试沙箱"""
import sys
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
from vercel_driver2 import api, TEAM2, PROJ2

c, r = api('DELETE', '/v2/sandboxes/victim1?teamId=%s&projectId=%s' % (TEAM2, PROJ2))
print('cleanup victim1:', c, r[:100])
