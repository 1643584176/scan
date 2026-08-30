# -*- coding: utf-8 -*-
"""恢复 npol1 沙箱 (resume 自动快照)"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

# resume 恢复
c, r = api('GET', '/v2/sandboxes/npol1?teamId=%s&projectId=%s&resume=true' % (TEAM, PROJ))
print('resume ->', c, flush=True)
d = json.loads(r)
sb = d.get('sandbox', {})
print('status:', sb.get('status'), 'sid:', sb.get('currentSessionId'), flush=True)
time.sleep(5)

# 再次查询确认 running
c, r = api('GET', '/v2/sandboxes/npol1?teamId=%s&projectId=%s' % (TEAM, PROJ))
d = json.loads(r)
sb = d.get('sandbox', {})
print('after resume status:', sb.get('status'), 'sid:', sb.get('currentSessionId'), flush=True)

print('=== RESUME DONE ===', flush=True)
