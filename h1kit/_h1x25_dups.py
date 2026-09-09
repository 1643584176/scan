# -*- coding: utf-8 -*-
"""h1x25: 提取 duplicates 字段定义 + HacktivitySearchQuery 全形状 + REST json 端点候选"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

t = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()
print('bundle len', len(t))

out = []
# 1. HacktivitySearchQuery 完整
for name in ['HacktivitySearchQuery']:
    for m in re.finditer(r'"((?:[^"\\]|\\.)*query ' + name + r'(?:[^"\\]|\\.)*?)"', t):
        s = m.group(1).replace('\\n', '\n').replace('\\"', '"')
        out.append(f'===== {name} len={len(s)} =====\n{s}\n')
        break

# 2. duplicates 字段在 selection 里出现的样子
for m in re.finditer(r'[a-zA-Z_]*duplicates[a-zA-Z_]*', t):
    pass
i = t.find('duplicates')
cnt = 0
while i != -1 and cnt < 5:
    out.append(f'--- duplicates ctx @{i} ---\n' + t[max(0,i-400):i+400].replace('\\n','\n')[:900] + '\n')
    cnt += 1
    i = t.find('duplicates', i+1)

# 3. REST json 端点候选(老版端点)
eps = set()
for m in re.finditer(r'"(/(?:reports|hacktivity|programs|teams|notifications|users|search|me)[a-zA-Z0-9_\-{}$./]*\.json)"', t):
    eps.add(m.group(1))
out.append('===== REST json 端点候选 =====')
for e in sorted(eps)[:40]:
    out.append(e)

open(r'D:\scan\h1kit\_h1x25_out.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('written', sum(len(x) for x in out))
