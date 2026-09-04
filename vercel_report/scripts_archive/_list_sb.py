# -*- coding: utf-8 -*-
"""列出所有沙箱: 名称/会话/状态/创建时间/镜像信息"""
import sys, os
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
import vercel_driver as vd

c, r = vd.list_sandboxes()
print('status', c)
if c != 200:
    print(r[:800])
    sys.exit(0)
import json
d = json.loads(r)
for sb in d.get('sandboxes', []):
    print('%-16s %-26s %-10s created=%s %s %s' % (
        sb.get('name'), sb.get('currentSessionId'), sb.get('status'),
        sb.get('createdAt'), sb.get('runtime'), sb.get('region')))
