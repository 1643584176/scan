# -*- coding: utf-8 -*-
import sys, time, json
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

# 删除 sdk46b (stopped + 快照占用存储配额)
c, r = api('DELETE', '/v2/sandboxes/sdk46b?teamId=%s&projectId=%s' % (TEAM, PROJ))
print('delete sdk46b:', c, (r or '')[:300])
time.sleep(3)

# 验证创建恢复
c, r = api('POST', '/v4/sandboxes?teamId=%s' % TEAM, {'projectId': PROJ, 'name': 'quota_probe2'}, 30)
print('create probe:', c)
print('body:', (r or '')[:300])
if c == 200:
    sid = json.loads(r)['sandbox']['currentSessionId']
    print('OK sid:', sid)
    time.sleep(2)
    c2, r2 = api('DELETE', '/v2/sandboxes/quota_probe2?teamId=%s&projectId=%s' % (TEAM, PROJ))
    print('cleanup:', c2)
