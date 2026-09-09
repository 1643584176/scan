# -*- coding: utf-8 -*-
"""h1x29: 找 hacktivity search 前端的真实 sort/direction 构造"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

t = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()
out = []

# direction 字面量出现
for m in re.finditer(r'direction:\s*"([A-Z]+)"', t):
    out.append('direction literal: ' + m.group(1))
# direction: `X` AST
for m in re.finditer(r'value:`direction`', t):
    seg = t[m.start():m.start()+300]
    mm = re.search(r'value:\{kind:`EnumValue`,value:`([^`]+)`\}', seg) or re.search(r'value:`([A-Z]+)`', seg)
    out.append('AST direction ctx: ' + (mm.group(1) if mm else seg[:150]))
    if len(out) > 12: break

out.append('')
# 找 search 的 sort 变量赋值(搜 "field" 且 "DESC"/"ASC" 同现的字面量对象)
for m in re.finditer(r'\{field:\s*"([^"]+)",\s*direction:\s*"([A-Z]+)"\}', t):
    out.append(f'sort obj: field={m.group(1)} direction={m.group(2)}')
for m in re.finditer(r'\{direction:\s*"([A-Z]+)",\s*field:\s*"([^"]+)"\}', t):
    out.append(f'sort obj2: field={m.group(2)} direction={m.group(1)}')

out.append('')
# CompleteHacktivityReportIndex 调用上下文(变量名 sort 从哪来)
i = t.find('CompleteHacktivityReportIndex')
while i != -1:
    seg = t[max(0, i-2500):i]
    if 'sort' in seg:
        m = re.search(r'(\w+)\s*[=:]\s*\{[^}]{0,200}\}', seg)
        out.append(f'--- near index ---')
        out.append(seg[-700:])
        break
    i = t.find('CompleteHacktivityReportIndex', i+1)

# 找 hacktivity 排序状态常量(常见 "sortField"/"NEWEST" 之类)
for kw in ['NEWEST', 'oldest', 'recent', 'trending', 'popular', 'upvotes', 'latest_disclosable_activity_at']:
    c = t.count(kw)
    if c:
        out.append(f'{kw}: {c}')
out.append('')
# latest_disclosable_activity_at 上下文(找它作为字符串在 query 构造的位置)
for m in re.finditer(r'latest_disclosable_activity_at', t):
    seg = t[max(0, m.start()-200):m.start()+200]
    out.append('ctx: ...' + seg.replace('\n', ' ')[:350] + '\n')
    if out.count('') > 0 and sum(1 for x in out if x.startswith('ctx')) >= 6: break

open(r'D:\scan\h1kit\_h1x29_out.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out)[:5500])
