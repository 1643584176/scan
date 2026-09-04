# -*- coding: utf-8 -*-
"""从 JS bundle 提取 DB 相关 API/分支/角色逻辑"""
import re

d = open(r'D:\scan\netlify_report\_js\net_app.js', encoding='utf-8', errors='ignore').read()

def show(label, pat, limit=25):
    print(f'==== {label} ====')
    seen = set()
    for m in re.finditer(pat, d):
        s = m.group(0)
        if s not in seen:
            seen.add(s)
            print(s[:200])
        if len(seen) >= limit:
            break

# 1) branch 相关 API 路径
show('BRANCH-PATHS', r'["\'][^"\']*branch[^"\']*["\']', 20)
# 2) drizzle-studio 加载 URL
show('DRIZZLE-SRC', r'https?://[^"\' ]{0,150}drizzle[^"\' ]{0,80}', 10)
# 3) database api 路径
show('DB-API', r'["\'][^"\']*(database|db-)[^"\']*["\']', 30)
