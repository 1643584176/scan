# -*- coding: utf-8 -*-
"""h1x6: 提取 report 相关 GraphQL 文档(字符串形式 query 全文)"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

t_app = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()

# 1. query/mutation/operation 名字清单
names = set()
for m in re.finditer(r'\b(?:query|mutation)\s+([A-Za-z_][A-Za-z0-9_]*)', t_app):
    names.add(m.group(1))
print('===== operation 名(前 120)=====')
for n in sorted(names)[:120]:
    print('  ', n)
print('total', len(names))

# 2. 字符串形式的 graphql 文档(report 相关)
print('===== report 相关文档字符串 =====')
for m in re.finditer(r'"(query|mutation)\s+[A-Za-z_][A-Za-z0-9_]*(?:[^"\\]|\\.)*?"', t_app):
    doc = m.group(0)
    if re.search(r'report|Report', doc):
        print(doc[:2000])
        print('---')
