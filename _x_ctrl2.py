# -*- coding: utf-8 -*-
"""控制面续: list-snapshots 范围 + fork 语义
C5: GET /v2/sandboxes/snapshots?teamId= -> 列表范围 (跨项目?)
C6: POST /v2/sandboxes/npol1/fork {projectId} -> fork 创建 (策略继承?)
C7: fork 后新沙箱 readback (networkPolicy 是否继承)
C8: 清理 fork 沙箱
"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

# C5: list snapshots
c, r = api('GET', '/v2/sandboxes/snapshots?teamId=%s' % TEAM)
print('[C5-list-snapshots] http=%s | %s' % (c, r[:600]), flush=True)

# C6: fork
c, r = api('POST', '/v2/sandboxes/npol1/fork?teamId=%s' % TEAM, {"projectId": PROJ})
print('[C6-fork] http=%s | %s' % (c, r[:400]), flush=True)
fork_name = None
fork_sid = None
try:
    dd = json.loads(r)
    fork_name = dd.get('name') or (dd.get('sandbox') or {}).get('name')
    fork_sid = (dd.get('sandbox') or {}).get('currentSessionId')
except Exception:
    pass
print('    fork name:', fork_name, 'sid:', fork_sid, flush=True)

# C7: fork 后状态
if fork_name:
    time.sleep(3)
    c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (fork_name, TEAM, PROJ))
    print('[C7-fork-readback] http=%s | %s' % (c, r[:500]), flush=True)
    # 删除清理
    c, r = api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (fork_name, TEAM, PROJ))
    print('[C8-fork-cleanup] http=%s | %s' % (c, r[:200]), flush=True)

print('=== CTRL2 DONE ===', flush=True)
