# -*- coding: utf-8 -*-
"""扫 net_app.js:database 管理功能(GraphQL mutation/query 名 + REST 路径 + branch 相关调用)"""
import re

data = open(r'D:\scan\netlify_report\_js\net_app.js', encoding='utf-8', errors='ignore').read()

# 1. branchId / database branch 相关上下文
print('== branchId 上下文 ==')
for m in re.finditer(r'branchId', data):
    i = m.start()
    ctx = data[max(0, i - 200):i + 200].replace('\n', ' ')
    print('  ...%s...' % ctx)
    print()

# 2. GraphQL 操作名(常见 database 前缀)
print('== 含 database 的驼峰标识符(前40) ==')
names = sorted(set(re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*(?:Database|database)[a-zA-Z0-9_]*', data)))
for n in names[:40]:
    print(' ', n)
