# -*- coding: utf-8 -*-
"""检查凭据定义与输出文件"""
import re, os

d = open(r'D:\scan\netlify_report\_net_creds.py', encoding='utf-8', errors='ignore').read()
for k in ['TOKEN_A', 'TOKEN_B', 'SITE_A', 'SITE_B']:
    m = re.search(k + r"\s*=\s*'([^']{0,80})", d)
    v = m.group(1) if m else 'NOT FOUND'
    print(k, '=', (v[:30] + '...len%d' % len(v)) if len(v) > 30 else v)

print()
print('== 相关输出文件 ==')
base = r'D:\scan\netlify_report'
for f in sorted(os.listdir(base)):
    if f.endswith(('_out.txt', '_out.json')) and any(x in f for x in ('dbq', 'pat', 'branch', 'snap', 'rotate', 'dbapi')):
        print(' ', f, os.path.getsize(os.path.join(base, f)))
