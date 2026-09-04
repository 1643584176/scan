# -*- coding: utf-8 -*-
"""openapi swagger 路径统计:总数/前缀分类/含敏感关键词的端点"""
import re, sys, collections

data = open(r'D:\scan\netlify_report\_openapi\swagger.yml', encoding='utf-8', errors='ignore').read()

paths = re.findall(r'^  (/[A-Za-z0-9_{}./\-]+):', data, re.M)
print('总路径数:', len(paths))

# 前缀分类
cats = collections.Counter()
for p in paths:
    seg = p.split('/')
    if len(seg) > 2:
        cats[seg[1]] += 1
    else:
        cats['<root>'] += 1
print('\n== 按第一段分类 ==')
for k, v in cats.most_common(40):
    print('  %-22s %d' % (k, v))

# database 相关
print('\n== 含 database/neon/postgres/connect 的路径 ==')
for p in paths:
    if re.search(r'database|neon|postgres|connect', p, re.I):
        print(' ', p)

# 有趣的新端点
print('\n== 含 secret/token/key/credential/snapshot/branch 的路径 ==')
for p in paths:
    if re.search(r'secret|token|key|credential|snapshot|branch', p, re.I):
        print(' ', p)
