# -*- coding: utf-8 -*-
"""h1x53r: bundle URL 端点全量提取 - 找前端实际调用的非 /graphql REST 路径"""
import re, sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
t = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()
print('bundle size:', len(t))

# 1. 字符串字面量中的路径模式(不以 http 开头、以 / 开头、含字母)
pat1 = re.compile(r'["\'`](/(?:api|v\d|reports|bugs|inbox|hai|graphql|attachments|notifications|hacktivity|opportunities|search|users|teams|org|internal|gateway)[A-Za-z0-9_\-/{}?&=\.$]*)["\'`]')
paths = {}
for m in pat1.finditer(t):
    p = m.group(1)
    # 去掉变量占位符归一化
    key = re.sub(r'\$\{[^}]*\}|\$\w+|\{id\}', '{X}', p)
    key = re.sub(r'=\$[A-Za-z]+|=\{[^}]*\}', '=V', key)
    paths.setdefault(key, 0)
    paths[key] += 1
print('\n===== 路径字面量(前 80) =====')
for p, c in sorted(paths.items(), key=lambda x: -x[1])[:80]:
    print(f'{c:5d}  {p}')

# 2. 完整 URL(http/https)
pat2 = re.compile(r'["\'`](https?://[A-Za-z0-9_.\-/]+)["\'`]')
urls = {}
for m in pat2.finditer(t):
    u = m.group(1)
    urls.setdefault(u, 0)
    urls[u] += 1
print('\n===== 完整 URL(前 40) =====')
for u, c in sorted(urls.items(), key=lambda x: -x[1])[:40]:
    print(f'{c:5d}  {u}')

# 3. fetch( 调用上下文
print('\n===== fetch( 调用样例(前 20) =====')
for m in list(re.finditer(r'fetch\(', t))[:20]:
    j = m.start()
    print('--- @', j)
    print(t[max(0, j-100):j+300].replace('\n', ' ')[:400])
    print()
