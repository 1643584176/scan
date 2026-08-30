# -*- coding: utf-8 -*-
"""victim 侧: 创建沙箱 + marker + 打快照 (供 attacker 快照 IDOR 测试)
用法: python victim_snap_setup.py <sbx_name>
输出: VICTIM_SID / MARKER / SNAPSHOT_ID
"""
import json, sys, time, uuid
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver2 import api, TEAM2, PROJ2

name = sys.argv[1]
marker = 'VICTIM_SNAP_MARKER_%s' % uuid.uuid4().hex[:12]

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

# 打快照 (session 会终止)
c, r = api('POST', '/v2/sandboxes/sessions/%s/snapshot?teamId=%s' % (sid, TEAM2),
           {'expiration': 86400000})
print('snapshot create:', c, r[:400], flush=True)
if c == 200:
    try:
        d = json.loads(r)
        snap = d.get('snapshot', {})
        snap_id = snap.get('id') or d.get('snapshotId')
        print('SNAPSHOT_ID:', snap_id, flush=True)
        print('snapshot meta:', json.dumps(snap)[:300], flush=True)
    except Exception as e:
        print('parse err:', e, r[:300], flush=True)

print('MARKER:', marker, flush=True)
print('=== VICTIM SNAPSHOT READY ===', flush=True)
