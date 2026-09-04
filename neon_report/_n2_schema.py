# -*- coding: utf-8 -*-
"""找 bucket 相关 schema 定义"""
import json
s = json.load(open(r'D:\scan\neon_report\_openapi_v2.json', encoding='utf-8'))
names = [n for n in s['components']['schemas'] if 'ucket' in n or 'resign' in n]
print('schema names:', names)
for n in names:
    print('\n=== %s ===' % n)
    print(json.dumps(s['components']['schemas'][n], indent=1)[:1500])
# 找 bucket 相关 path 的请求体引用
for p, ops in s['paths'].items():
    if 'bucket' in p.lower():
        for m, o in ops.items():
            if isinstance(o, dict) and 'requestBody' in o:
                print('\nPATH %s %s -> %s' % (m.upper(), p, json.dumps(o['requestBody'])[:400]))
