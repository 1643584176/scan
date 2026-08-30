# -*- coding: utf-8 -*-
"""E 线: 快照跨沙箱恢复测试 (核心)
前提: fb90x3 快照 snap_GeI4aPOtJVfXdRFNUSypVff4Rdk8 (250MB, 含 fb90x3 磁盘状态)
测试: resume scanl4 (或新沙箱) 时指定该快照 -> 若 currentSnapshotId=GeI4a 则跨沙箱快照恢复可行
"""
import sys, json, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

FB90_SNAP = 'snap_GeI4aPOtJVfXdRFNUSypVff4Rdk8'   # fb90x3 的快照 (刚创建)
# scanl4 历史快照 (昨天创建, 含 vda 挂载实验现场?)
SCANL4_SNAP = 'snap_UAnwFE0ZIBYAqQwseb4jiNRs2iDx'

print('=== 1) resume scanl4 + 指定 fb90x3 的快照 ===')
c, r = api('GET', '/v2/sandboxes/scanl4?teamId=%s&projectId=%s&resume=true&snapshotId=%s' % (TEAM, PROJ, FB90_SNAP))
print(' -> %d' % c)
try:
    d = json.loads(r)
    sb = d.get('sandbox', {})
    print(' currentSnapshotId =', sb.get('currentSnapshotId'))
    print(' currentSessionId  =', sb.get('currentSessionId'))
    print(' status =', sb.get('status'))
except Exception as e:
    print(' parse err:', e, r[:500])

print()
print('=== 2) resume scanl4 + 指定 scanl4 自己的历史快照 ===')
c, r = api('GET', '/v2/sandboxes/scanl4?teamId=%s&projectId=%s&resume=true&snapshotId=%s' % (TEAM, PROJ, SCANL4_SNAP))
print(' -> %d' % c)
try:
    d = json.loads(r)
    sb = d.get('sandbox', {})
    print(' currentSnapshotId =', sb.get('currentSnapshotId'))
except Exception as e:
    print(' parse err:', e, r[:500])
