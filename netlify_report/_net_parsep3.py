# -*- coding: utf-8 -*-
"""解析 probe3 输出,聚焦:metadata API 探测结果 / 出网 / fs 深探"""
import json

d = json.load(open(r'D:\scan\netlify_report\_probe3_out.json', encoding='utf-8'))

print('=== env(非敏感简略)===')
for k in sorted(d.get('env', {})):
    v = d['env'][k]
    if any(s in k for s in ('TOKEN', 'SECRET', 'KEY', 'CRED')):
        print(' %s = %s' % (k, v[:60]))
    else:
        print(' %s = %s' % (k, v[:100]))

print()
print('=== metadata API(169.254.100.1:9001)===')
for m in d.get('meta', []):
    print(' ', m[:160])

print()
print('=== 出网 ===')
for n in d.get('net', []):
    print(' ', n[:200])

print()
print('=== fs ===')
for k, v in d.get('fs', {}).items():
    print(' %s: %s' % (k, str(v)[:400]))
