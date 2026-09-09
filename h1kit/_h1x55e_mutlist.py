# -*- coding: utf-8 -*-
"""h1x55e: bundle 提取全部 mutation 文档 - 返回数据型筛选"""
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
data = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='replace').read()
# 1) GraphQL 文档字符串形式的 mutation: "mutation Xxx(" 后跟可见结构
mut = re.findall(r'mutation\s+([A-Za-z0-9_]+)\s*\(([^)]{0,400}?)\)\s*\{', data)
print('### doc-string mutation count:', len(mut))
seen = set()
for name, args in mut:
    if name in seen:
        continue
    seen.add(name)
    print('MUT', name, '|', args[:150].replace('\n', ' '))
# 2) AST 形态 mutation
print()
print('### AST mutation count:')
ast = re.findall(r'operation:`mutation`,name:\{kind:`Name`,value:`([A-Za-z0-9_]+)`\}', data)
cnt = {}
for n in ast:
    cnt[n] = cnt.get(n, 0) + 1
print('AST total:', sum(cnt.values()), 'unique:', len(cnt))
missing = [n for n in cnt if n not in seen]
print('AST-only (not in doc strings) unique:', len(missing))
for n in sorted(missing):
    print('  AST-ONLY', n, 'x%d' % cnt[n])
