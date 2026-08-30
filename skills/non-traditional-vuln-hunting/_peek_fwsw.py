# -*- coding: utf-8 -*-
"""查看 allowcmp 沙箱 fwsw1.out 内容"""
import sys, os
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
from vercel_driver import api, cmd, TEAM, PROJ

c, r = api('GET', '/v2/sandboxes/allowcmp?teamId=%s&projectId=%s&resume=true' % (TEAM, PROJ))
print('resume:', c)
if c != 200:
    print(r[:200])
    sys.exit(1)
import json
sid = json.loads(r)['sandbox']['currentSessionId']
print('sid:', sid)
c, r = cmd(sid, 'cat', ['/vercel/sandbox/fwsw1.out'], timeout_ms=30000)
print('status:', c)
print(r[:2000])
