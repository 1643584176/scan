# -*- coding: utf-8 -*-
"""h1x26: 找 DuplicatesItemReport 引用者 + ctx@2976214 所属 operation + hacktivity sort 真实值"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

t = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()

out = []
# 1. DuplicatesItemReport 被哪个 operation 引用:搜其名字在 AST OperationDefinition 中出现的位置,回溯最近的 operation name
for m in re.finditer(r'DuplicatesItemReport', t):
    start = m.start()
    seg = t[max(0, start-3000):start]
    # 找最近的 OperationDefinition 的 name value
    names = re.findall(r'name:\{kind:`Name`,value:`([^`]+)`\}', seg)
    ops = re.findall(r'OperationDefinition', seg)
    if ops:
        # 回溯到最后一个 operation
        last_op = seg.rfind('OperationDefinition')
        after = seg[last_op:]
        nm = re.search(r'name:\{kind:`Name`,value:`([^`]+)`\}', after)
        opname = nm.group(1) if nm else '?'
        out.append(f'DuplicatesItemReport @{start} refs op={opname} (fragments near: {names[-3:]})')
        break  # 只要第一个(大概率就一个 operation)

# 2. ctx@2976214 上下文:找含 original_report 的 operation
i = t.find('original_report')
while i != -1:
    seg = t[max(0, i-20000):i]
    ops = re.findall(r'name:\{kind:`Name`,value:`([^`]+)`\}', seg)
    # 回溯 operation name:找最后一个 "operation:`query`" 后的 name
    m2 = re.findall(r'operation:`(query|mutation)`,name:\{kind:`Name`,value:`([^`]+)`\}', seg)
    if m2:
        out.append(f'original_report @{i}: op={m2[-1]}')
        break
    i = t.find('original_report', i+1)

# 3. 前端实际调用 HacktivitySearchQuery 的 sort 值/变量
i = t.find('HacktivitySearchQuery')
while i != -1:
    seg = t[max(0, i-1500):i]
    if 'sort' in seg and 'field' in seg:
        out.append('--- ctx near HacktivitySearchQuery ---')
        out.append(seg[-800:])
        break
    i = t.find('HacktivitySearchQuery', i+1)

# sort:{field 字面量
for m in re.finditer(r'sort:\s*\{\s*field:\s*"([^"]+)"', t):
    out.append('sort field literal: ' + m.group(1))
# 或者 AST 形式 field:{kind:`Name`,value:`X`}? sort 变量形式更多。查 SortInput 枚举引用:search(reporter_filter
out.append('--- reporter_filter 出现次数: ' + str(t.count('reporter_filter')))

open(r'D:\scan\h1kit\_h1x26_out.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out)[:4000])
