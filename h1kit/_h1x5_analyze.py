# -*- coding: utf-8 -*-
"""h1x5: bundle 端点分析 — graphql/api 路径 + report 查询"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

t_app = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()
t_const = open(r'D:\scan\h1kit\_h1x3_constants.js', encoding='utf-8', errors='ignore').read()

print('===== graphql 相关 =====')
for m in list(re.finditer(r'graphql', t_app, re.I))[:10]:
    i = m.start()
    print('...', t_app[max(0,i-150):i+150].replace('\n', ' ')[:320])
    print()

print('===== 常见 api 路径片段 =====')
for pat in [r'["\'`](/api/[a-zA-Z0-9_${}/.-]{2,60})["\'`]', r'["\'`](/graphql[a-zA-Z0-9_${}/.-]*)["\'`]']:
    hits = set(re.findall(pat, t_app))
    for h in sorted(hits)[:40]:
        print('  ', h)

print('===== 网络层端点常量 (url 构造) =====')
for m in list(re.finditer(r'(url|endpoint|baseUrl|apiUrl|graphqlUrl)[^,;]{0,80}', t_app))[:20]:
    print('  ', m.group(0)[:140])
