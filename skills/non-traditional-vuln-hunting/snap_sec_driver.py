# -*- coding: utf-8 -*-
"""E 线: 快照安全测试驱动 (控制面 API)
1) 快照创建: 自己 running session -> 200? 返回结构?
2) 快照创建 IDOR: 随机 sessionId / 已删沙箱 sessionId -> 404 or 200?
3) resume 指定 snapshotId: 跨 name 快照恢复 (快照 IDOR 前提)
4) 快照列表/详情端点枚举
"""
import sys, json, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

MY_SID = 'sbx_rYBK1EDcW4A8syrM6tFkQKoM7oJT'      # fb90x3 running
DEL_SID = 'sbx_b2TeTovZudMJHqzATCLk5iERq8qi'     # exp_idor 已删除沙箱的旧 sid
RAND_SID = 'sbx_zzz_notexist_zzz'

print('=== 1) 自己 session 创建快照 (fb90x3) ===')
for body in [None, {}, {'name': 'sec_test'}, {'description': 'sec test'}, {'snapshot': {}}]:
    c, r = api('POST', '/v2/sandboxes/sessions/%s/snapshot?teamId=%s' % (MY_SID, TEAM), body)
    print('  body=%s -> %d %s' % (body, c, r[:300]))
    if c == 200:
        print('  FULL:', r[:1500])
        break
    time.sleep(1)

print()
print('=== 2) 快照创建 IDOR: 已删沙箱旧 sid ===')
c, r = api('POST', '/v2/sandboxes/sessions/%s/snapshot?teamId=%s' % (DEL_SID, TEAM), {})
print('  deleted-sid -> %d %s' % (c, r[:300]))

print()
print('=== 3) 快照创建 IDOR: 随机 sid ===')
c, r = api('POST', '/v2/sandboxes/sessions/%s/snapshot?teamId=%s' % (RAND_SID, TEAM), {})
print('  rand-sid -> %d %s' % (c, r[:300]))

print()
print('=== 4) resume 指定 snapshotId ===')
c, r = api('GET', '/v2/sandboxes/scanl4?teamId=%s&projectId=%s&resume=true&snapshotId=snap_zzz' % (TEAM, PROJ))
print('  resume+snapshotId -> %d %s' % (c, r[:400]))

print()
print('=== 5) 快照列表/详情端点枚举 ===')
for ep in ['/v2/sandboxes/sessions/%s/snapshots' % MY_SID,
           '/v2/sandboxes/sessions/%s/snapshot' % MY_SID,
           '/v2/sandboxes/%s/snapshots' % 'fb90x3',
           '/v2/snapshots/snap_UAnwFE0ZIBYAqQwseb4jiNRs2iDx']:
    c, r = api('GET', ep + '?teamId=%s&projectId=%s' % (TEAM, PROJ))
    print('  GET %s -> %d %s' % (ep, c, r[:250]))
