# -*- coding: utf-8 -*-
"""h1x32: 本地查 ActivitiesBugDuplicate 字段(报告页 dup 活动是否引用原报告对象)"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
t = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()
out = []
for name in ['ActivitiesBugDuplicate', 'ActivitiesComment', 'ActivitiesBugFiled']:
    # AST fragment/type 上下文
    i = t.find('ActivitiesBugDuplicate')
    while i != -1:
        seg = t[max(0, i-200):i+1500]
        # 找 selectionSet 里字段名
        fields = re.findall(r'name:\{kind:`Name`,value:`([^`]+)`\}', seg)
        out.append(f'--- {name} @{i} fields: {fields[:25]}')
        break
    i = t.find('ActivitiesBugDuplicate', i+1)
    # 字符串 query 形式
    for m in re.finditer(r'"(?:[^"\\]|\\.)*ActivitiesBugDuplicate(?:[^"\\]|\\.)*?"', t):
        s = m.group(0).replace('\\n', '\n')[:1200]
        out.append(f'--- {name} string form:')
        out.append(s)
        break
open(r'D:\scan\h1kit\_h1x32_out.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out)[:3000])
