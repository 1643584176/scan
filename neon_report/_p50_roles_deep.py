# -*- coding: utf-8 -*-
"""Roles chunk: listProvisionedInstanceRoles 调用处前后 1200 字符
+ 该 chunk 内所有含 api 或 http 或 ${ 的字符串字面量
"""
import re, os

here = os.path.dirname(os.path.abspath(__file__))
d = os.path.join(here, '_js', 'prod_chunks')
src = open(os.path.join(d, 'ProvisionedInstancesItemRoles-BFeEbS-M.js'), encoding='utf-8', errors='replace').read()
out = []
out.append('=== size %d ===' % len(src))
for m in re.finditer(r'listProvisionedInstanceRoles', src):
    i = m.start()
    out.append('--- CALL ctx @%d ---' % i)
    out.append(src[max(0, i - 600):i + 600].replace('\n', ' '))

out.append('=== chunk 内 url/http/api 字面量 ===')
for m in re.finditer(r'["\'`]([^"\'`]{0,20}(?:/api/|api\.|http|\.build|\.tech|\.com|\.neon|neon\.)[^"\'`]{0,100})["\'`]', src):
    out.append(m.group(1)[:140])

out.append('=== chunk 内 import 行 ===')
for m in re.finditer(r'import\{[^}]{0,400}\}from"[^"]{1,80}"', src[:8000]):
    out.append(m.group(0)[:500])

p2 = os.path.join(here, '_p50_out.txt')
open(p2, 'w', encoding='utf-8').write('\n'.join(out))
print('done, lines:', len(out), flush=True)
