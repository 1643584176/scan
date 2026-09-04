# -*- coding: utf-8 -*-
"""Roles chunk import 段 -> 找 T 来源模块 -> 顺藤摸瓜"""
import re, os

here = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(here, '_js', 'prod_chunks', 'ProvisionedInstancesItemRoles-BFeEbS-M.js')
src = open(p, encoding='utf-8', errors='replace').read()
print('=== Roles chunk import 段(前 2500) ===', flush=True)
print(src[:2500], flush=True)
print('\n=== 找 T 的 import 绑定 ===', flush=True)
m = re.search(r'import\{([^}]*)\}from"\./([^"]+)"', src[:4000])
for mm in re.finditer(r'import\{([^}]*)\}from"\./([^"]+)"', src[:4000]):
    bind = mm.group(1)
    if re.search(r'\bT\b', bind):
        print('FOUND T in:', bind, 'from', mm.group(2), flush=True)
