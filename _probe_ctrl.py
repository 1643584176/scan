# -*- coding: utf-8 -*-
"""E 线: 控制面 REST API 缺陷快速测试 (只读, 零沙箱成本)
1) 沙箱 IDOR: 未知/他人沙箱名 resume/get
2) 快照端点枚举
3) 生命周期: 已删除沙箱的 session cmd
4) 权限: teamId 缺失/错误"""
import sys, json, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api

TEAM = 'team_GIy1SZ444lspqeNbh4r8uAUg'
PROJ = 'prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F'

print('=== 1) 未知沙箱名 resume ===')
c, r = api('GET', '/v2/sandboxes/zzz_notexist_zzz?teamId=%s&projectId=%s&resume=true' % (TEAM, PROJ))
print(c, r[:300])

print('=== 2) 无 teamId (默认 team?) ===')
c, r = api('GET', '/v2/sandboxes?limit=5')
print(c, r[:400])

print('=== 3) 快照端点 ===')
for ep in ['/v2/sandboxes/scanl4/snapshots',
           '/v2/sandboxes/snapshots',
           '/v2/snapshots']:
    c, r = api('GET', ep + '?teamId=%s&projectId=%s' % (TEAM, PROJ))
    print(ep, '->', c, r[:250])

print('=== 4) 已删沙箱 session cmd (生命周期) ===')
# 用刚删掉的 fb90x 类沙箱名测试: 先确认不存在
c, r = api('GET', '/v2/sandboxes/nosuchsb1?teamId=%s&projectId=%s' % (TEAM, PROJ))
print('get nosuchsb1:', c, r[:200])

print('=== 5) 错误 teamId ===')
c, r = api('GET', '/v2/sandboxes?teamId=team_zzz&project=%s' % PROJ)
print(c, r[:300])

print('=== 6) 项目隔离: 用他人 projectId ===')
c, r = api('GET', '/v2/sandboxes?teamId=%s&project=prj_zzz' % TEAM)
print(c, r[:300])

print('=== 7) snapshot 详情 (scanl4 的快照) ===')
c, r = api('GET', '/v2/snapshots/snap_UAnwFE0ZIBYAqQwseb4jiNRs2iDx?teamId=%s' % TEAM)
print(c, r[:400])
