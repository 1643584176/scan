# -*- coding: utf-8 -*-
"""验证配额恢复: 列出沙箱 + 创建测试沙箱"""
import sys, json, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
from vercel_driver import api, cmd, fresh_sandbox, TEAM, PROJ

c, r = api('GET', '/v2/sandboxes?teamId=%s&project=%s&limit=50' % (TEAM, PROJ))
print('list:', c, r[:300])

try:
    sid = fresh_sandbox('quota_test', network_mode='deny-all')
    print('CREATE OK sid:', sid)
    c, r = cmd(sid, 'echo', ['hello'], timeout_ms=20000)
    print('cmd:', c, r[:200])
except Exception as e:
    print('CREATE FAIL:', e)
