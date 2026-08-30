# -*- coding: utf-8 -*-
"""控制面剩余端点快速验证: snapshot 创建/get + fork 语义
C1: POST /v2/sandboxes/sessions/{sid}/snapshot -> 创建快照 (格式/authz)
C2: GET /v2/sandboxes/snapshots/{id}            -> 读快照 (authz)
C3: POST /v2/sandboxes/{name}/fork              -> fork 语义 (策略继承?)
C4: GET /v2/sandboxes/sessions/{sid}            -> 会话详情字段
"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

c, r = api('GET', '/v2/sandboxes/npol1?teamId=%s&projectId=%s' % (TEAM, PROJ))
d = json.loads(r)
sid = d['sandbox']['currentSessionId']
print('npol1 sid:', sid, 'status:', d['sandbox']['status'], flush=True)
if d['sandbox'].get('status') != 'running':
    c, r = api('GET', '/v2/sandboxes/npol1?teamId=%s&projectId=%s&resume=true' % (TEAM, PROJ))
    d = json.loads(r)
    sid = d['sandbox']['currentSessionId']
    print('resumed sid:', sid, flush=True)
    time.sleep(5)

# C1: 创建快照
c, r = api('POST', '/v2/sandboxes/sessions/%s/snapshot?teamId=%s' % (sid, TEAM), {})
print('[C1-snapshot] http=%s | %s' % (c, r[:400]), flush=True)
snap_id = None
try:
    dd = json.loads(r)
    snap_id = dd.get('id') or (dd.get('snapshot') or {}).get('id')
except Exception:
    pass
print('    snapshot id:', snap_id, flush=True)

# C2: 读快照
if snap_id:
    c, r = api('GET', '/v2/sandboxes/snapshots/%s?teamId=%s' % (snap_id, TEAM))
    print('[C2-get-snapshot] http=%s | %s' % (c, r[:300]), flush=True)

# C3: fork (npol1 当前策略可能非 allow-all, fork 观察是否继承)
c, r = api('POST', '/v2/sandboxes/npol1/fork?teamId=%s' % TEAM, {})
print('[C3-fork] http=%s | %s' % (c, r[:400]), flush=True)
fork_name = None
try:
    dd = json.loads(r)
    fork_name = dd.get('name') or (dd.get('sandbox') or {}).get('name')
except Exception:
    pass
print('    fork name:', fork_name, flush=True)

# C4: 会话详情
c, r = api('GET', '/v2/sandboxes/sessions/%s?teamId=%s' % (sid, TEAM))
print('[C4-session] http=%s | %s' % (c, r[:500]), flush=True)

print('=== CTRL DONE ===', flush=True)
