# -*- coding: utf-8 -*-
"""h1x28: 找 SortInput 枚举值/前端 sort 变量构造 + search 调用上下文"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

t = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()
out = []

# 1. 所有含 disclosable/latest 的字段字面量候选
for kw in ['latest_disclosable_activity_at', 'latest_disclosable_action', 'disclosed_at', 'submitted_at']:
    out.append(f'{kw}: count={t.count(kw)}')
out.append('')

# 2. SortInput enum 定义:Hasura schema 常见 "enum SortInput" 或 sort:{field:...} 构造
for m in re.finditer(r'sort:\s*\{\s*field:\s*([^,}]{1,60})', t):
    s = m.group(1)
    if 'value' in s or 'String' in s or len(s) < 45:
        out.append('sort field construct: ' + s[:80])
out.append('')
# AST 形式 value:`X` 紧跟 sort
for m in re.finditer(r'value:`sort`[^}]{0,400}', t):
    out.append('AST sort ctx: ' + m.group(0)[:400])
    break

# 3. GraphQL 文本里的 sort enum:"enum SortInput" 或 value:"..."(枚举值通常是字符串数组)
i = t.find('SortInput')
cnt = 0
while i != -1 and cnt < 8:
    seg = t[i:i+900]
    out.append(f'--- SortInput ctx @{i} ---\n' + seg[:900] + '\n')
    cnt += 1
    i = t.find('SortInput', i+1)

open(r'D:\scan\h1kit\_h1x28_out.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out)[:5000])
