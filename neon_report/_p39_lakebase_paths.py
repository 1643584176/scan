# -*- coding: utf-8 -*-
"""prod_app.js: lakebase/workspace/databricks 连接管理相关 Neon API 端点提取"""
import re, os

here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, '_js', 'prod_app.js'), encoding='utf-8', errors='replace').read()

# lakebase 相关 URL 字符串(/api/ 或 /ajax-api 或 workspace/lakebase/connection 等)
seen = set()
for m in re.finditer(r'["\'`](/[^"\'`]*(?:lakebase|workspace|databricks|observability|connection|genie|insight)[^"\'`]*)["\'`]', src):
    s = m.group(1)
    if s not in seen and len(s) < 160:
        seen.add(s)
print('=== lakebase/workspace 相关路径字符串 ===', flush=True)
for s in sorted(seen):
    print(s, flush=True)

# 含 api 前缀的
seen2 = set()
for m in re.finditer(r'["\'`](/api/[^"\'`]{2,140})["\'`]', src):
    s = m.group(1)
    if any(k in s.lower() for k in ['lakebase', 'workspace', 'databrick', 'observ', 'insight', 'genie', 'connector', 'integrat']):
        if s not in seen2:
            seen2.add(s)
print('\n=== /api/ lakebase 家族 ===', flush=True)
for s in sorted(seen2):
    print(s, flush=True)
