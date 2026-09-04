# -*- coding: utf-8 -*-
"""扫 net_app.js:所有 /sites/{...}/database/* 子路径与 queryFn 映射"""
import re

data = open(r'D:\scan\netlify_report\_js\net_app.js', encoding='utf-8', errors='ignore').read()

# 1. 所有 database 子路径(拼接模式)
print('== /database/* 子路径(concat 模式) ==')
for m in sorted(set(re.findall(r'/database/[A-Za-z0-9_\-\$\.{}]+', data))):
    print(' ', m)

# 2. databaseSnapshots / databaseSettings / databaseTimeSeries 等 queryKey 定义处附近的 request 路径
print()
print('== queryKey 函数 -> queryFn 路径 ==')
for kw in ['databaseSnapshots', 'databaseSettings', 'databaseTimeSeries', 'databaseComputeSettings',
           'databaseBranchDeploys']:
    i = data.find(kw)
    if i < 0:
        continue
    seg = data[max(0, i - 300):i + 300].replace('\n', ' ')
    print('-- %s --' % kw)
    print('  %s' % seg)
    print()
