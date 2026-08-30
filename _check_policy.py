# -*- coding: utf-8 -*-
"""查询沙箱详情确认 networkPolicy 设置"""
import sys, json
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
from vercel_driver import api, TEAM, PROJ

for name in ['udpb1', 'quota_test']:
    c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (name, TEAM, PROJ))
    print('=== %s -> %d' % (name, c))
    if c == 200:
        d = json.loads(r)
        sb = d.get('sandbox', d)
        # 打印所有与 network/policy 相关的字段
        for k, v in sb.items():
            if 'network' in k.lower() or 'policy' in k.lower() or 'firewall' in k.lower():
                print('  %s: %s' % (k, v))
        print('  keys:', sorted(sb.keys()))
    else:
        print(' ', r[:300])
