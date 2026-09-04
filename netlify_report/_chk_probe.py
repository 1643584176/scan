# -*- coding: utf-8 -*-
import os, re
base = r'D:\scan\netlify_report'
# 1. _gql_find.py 状态
p = os.path.join(base, '_gql_find.py')
if os.path.exists(p):
    t = open(p, encoding='utf-8', errors='replace').read()
    print('=== _gql_find.py head ===')
    print(t[:1500])
else:
    print('no _gql_find.py')
print()
# 2. probe 系列的模块使用(child_process?)
for f in sorted(os.listdir(base)):
    if f.startswith('_fn_probe') and f.endswith('.js'):
        t = open(os.path.join(base, f), encoding='utf-8', errors='replace').read()
        mods = sorted(set(re.findall(r"require\(['\"]([a-z0-9_/-]+)['\"]\)", t)))
        print(f, '->', mods)
