# -*- coding: utf-8 -*-
"""h1x8: 提取 ReportPage / ReportTimelineMainQuery 定义(变量+字段)"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

t_app = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()

for target in ['ReportPage', 'ReportTimelineMainQuery']:
    idxs = [m.start() for m in re.finditer(re.escape(target), t_app)]
    print(f'===== {target}: {len(idxs)} hits =====')
    for i in idxs[:4]:
        seg = t_app[max(0, i-300):i+1500]
        # 找 definition/variableDefinitions/name.value
        print(f'--- @{i} ---')
        print(seg.replace('\n', ' ')[:1700])
        print()

# 找 variableDefinitions 里的 database_id 模式(query 变量)
print('===== database_id 变量出现处(前5)=====')
for m in list(re.finditer(r'database_id', t_app))[:5]:
    i = m.start()
    print('@', i, ':', t_app[max(0,i-400):i+200].replace('\n', ' ')[:600])
    print()
