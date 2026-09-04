# -*- coding: utf-8 -*-
"""useCurrentProvisionedInstance-BkyxKEkQ.js 全量内容分析: 找 API 调用/URL/方法"""
import re, os

here = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(here, '_js', 'prod_chunks', 'useCurrentProvisionedInstance-BkyxKEkQ.js')
src = open(p, encoding='utf-8', errors='replace').read()
print('size:', len(src), flush=True)
out = []
# import 行
for m in re.finditer(r'import\{[^}]{0,300}\}from"[^"]{1,60}"', src[:6000]):
    out.append('IMPORT: ' + m.group(0)[:400])
# 所有字符串字面量(>8 字符, 含斜杠或点)
for m in re.finditer(r'["\'`]([A-Za-z0-9_\-/.${}:]{8,140})["\'`]', src):
    s = m.group(1)
    if any(k in s for k in ['/', '.', 'get', 'list', 'instance', 'api', 'use', 'provision']):
        out.append('STR: ' + s)
# api client 方法调用形态: Xxx.method( 或 .method 在 queryFn 里
open(os.path.join(here, '_p55_out.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('lines:', len(out), flush=True)
