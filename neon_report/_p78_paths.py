# -*- coding: utf-8 -*-
"""bat 类内全部 path 字符串提取 -> 找 database_instance/lakebase 相关端点 + 全端点清单"""
import re, os

here = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(here, '_js', 'prod_chunks', 'index-LpJ7SKi1.js')
src = open(p, encoding='utf-8', errors='replace').read()

i_bat = src.find('class bat extends yat')
i_kde = src.find('const Kde')
seg = src[i_bat:i_kde]

out = []
# path:"/xxx" 和 path:`/xxx${...}` 形态
paths = set()
for m in re.finditer(r'path:\s*("([^"]+)"|`([^`]+)`)', seg):
    paths.add(m.group(2) or m.group(3))
out.append('total paths in bat: %d' % len(paths))
# 含 instance/lakebase/database/catalog/role/permission/resolve 的
hit = sorted(p for p in paths if any(k in p.lower() for k in
    ['instance', 'lakebase', 'database', 'catalog', 'resolve', 'provision', 'credential', 'oauth', 'workspace', 'sql']))
out.append('=== 相关路径(%d) ===' % len(hit))
for p in hit:
    out.append(p)

# 方法数(两种形态)
m1 = re.findall(r'([A-Za-z_$][\w$]*)=\(', seg)
m2 = re.findall(r'^\s*([A-Za-z_$][\w$]*)\(', seg, re.M)
out.append('arrow-field methods: %d, method-style: %d' % (len(m1), len(m2)))

open(os.path.join(here, '_p78_out.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('done lines:', len(out), flush=True)
