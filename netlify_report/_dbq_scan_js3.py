# -*- coding: utf-8 -*-
"""扫 net_app.js:找 database 相关 REST 路径与 GraphQL 查询"""
import re

data = open(r'D:\scan\netlify_report\_js\net_app.js', encoding='utf-8', errors='ignore').read()

# 1. 所有 REST-ish 路径(含 database 的)
print('== 含 database 的 API 路径 ==')
paths = sorted(set(re.findall(r'"(/[A-Za-z0-9_\-\$:\.{}]*(?:database|Database)[A-Za-z0-9_\-\$:\.{}]*)"', data)))
for p in paths:
    print(' ', p)

# 2. rotate_credentials 上下文
print()
print('== rotate_credentials 上下文 ==')
for m in re.finditer(r'rotate_credentials', data):
    i = m.start()
    print('  ...%s...' % data[max(0, i - 300):i + 300].replace('\n', ' '))
    print()

# 3. connection_strings / has_database 上下文(数据源)
print('== connection_strings 上下文(前3) ==')
cnt = 0
for m in re.finditer(r'connection_strings', data):
    if cnt >= 3:
        break
    i = m.start()
    print('  ...%s...' % data[max(0, i - 250):i + 250].replace('\n', ' '))
    print()
    cnt += 1
