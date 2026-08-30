# -*- coding: utf-8 -*-
"""victim 侧: 创建沙箱 + 放置跨租户 marker
用法: python victim_setup.py <sbx_name>
输出: victim sandbox sid + marker 内容
"""
import json, sys, time, uuid
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver2 import api, TEAM2, PROJ2

name = sys.argv[1]
marker = 'VICTIM_MARKER_%s' % uuid.uuid4().hex[:12]

# 删除同名旧沙箱 (如有)
api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (name, TEAM2, PROJ2))
time.sleep(2)

c, r = api('POST', '/v2/sandboxes?teamId=%s' % TEAM2,
           {'projectId': PROJ2, 'name': name})
print('create victim sandbox:', c, r[:300], flush=True)
if c != 200:
    raise RuntimeError(r[:300])
sid = json.loads(r)['sandbox']['currentSessionId']
print('VICTIM_SID:', sid, flush=True)
time.sleep(2)

# 放置 marker
c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM2),
           {'command': 'sh', 'args': ['-c', 'echo %s > /vercel/sandbox/tenant_marker.txt && cat /vercel/sandbox/tenant_marker.txt' % marker],
            'wait': True, 'timeout': 30000})
print('marker write:', c, r[:200], flush=True)

# 回读确认
c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM2),
           {'command': 'cat', 'args': ['/vercel/sandbox/tenant_marker.txt'], 'wait': True, 'timeout': 30000})
print('marker readback:', c, r[:200], flush=True)

print('MARKER:', marker, flush=True)
print('=== VICTIM READY ===', flush=True)
