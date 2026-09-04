# -*- coding: utf-8 -*-
"""prod_app.js 深度: 找 so 定义(instance baseURL) / databricks SDK 痕迹 / lakebase 主机"""
import re, os

here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, '_js', 'prod_app.js'), encoding='utf-8', errors='replace').read()

# 1. so 定义: 搜 so= 后跟 {instance 或 instance= 
for m in re.finditer(r'\bso\s*=\s*\{', src):
    i = m.start()
    seg = src[i:i + 400]
    if 'instance' in seg or 'Observability' in seg:
        print('SO-DEF:', seg[:350].replace('\n', ' '), flush=True)

# 2. axios.create 配置(baseURL)
cands = []
for m in re.finditer(r'(?:axios)?\.create\(\{', src):
    i = m.start()
    seg = src[i:i + 300]
    if 'baseURL' in seg or 'instance' in seg:
        cands.append(seg[:280].replace('\n', ' '))
for c in cands[:8]:
    print('CREATE:', c, flush=True)

# 3. databricks / lakebase 主机引用
for kw in ['databricks', 'lakebase', 'DBSQLX']:
    idxs = [m.start() for m in re.finditer(kw, src)]
    print('KW', kw, '->', len(idxs), flush=True)
    for i in idxs[:3]:
        seg = src[max(0, i - 200):i + 300].replace('\n', ' ')
        hosts = re.findall(r'https?://[a-zA-Z0-9._-]+', src[max(0, i - 800):i + 800])
        print('  hosts nearby:', set(hosts), flush=True)
        print('  ', seg[:400], flush=True)
