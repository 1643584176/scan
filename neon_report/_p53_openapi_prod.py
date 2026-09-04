# -*- coding: utf-8 -*-
"""抓 neon.com/api_spec/release/v2.json 最新版, 搜 provisioned instance / database instance 端点"""
import http.client, ssl, json, re

ctx = ssl.create_default_context()
conn = http.client.HTTPSConnection('neon.com', context=ctx, timeout=60)
conn.request('GET', '/api_spec/release/v2.json', headers={'User-Agent': 'Mozilla/5.0'})
r = conn.getresponse(); raw = r.read(); conn.close()
print('status:', r.status, 'len:', len(raw), flush=True)
if r.status != 200:
    raise SystemExit

spec = json.loads(raw)
print('openapi:', spec.get('openapi'), flush=True)
paths = spec.get('paths', {})
print('paths total:', len(paths), flush=True)

# 1. 含 instance / lakebase / catalog 的路径
keys = sorted(paths.keys())
hit = [p for p in keys if any(k in p.lower() for k in ['instance', 'lakebase', 'catalog', 'provision'])]
print('=== instance/lakebase/catalog 相关路径(%d) ===' % len(hit), flush=True)
for p in hit:
    print(p, '->', ','.join(m for m in paths[p] if m in ('get', 'post', 'put', 'patch', 'delete')), flush=True)

# 2. 最近新增端点信号: 全部路径数 vs 本地旧 spec
local = json.load(open(r'D:\scan\neon_report\_openapi_v2.json', encoding='utf-8'))
lp = set(local.get('paths', {}).keys())
np = set(keys)
print('=== 新旧 diff: 新 spec 独有路径 %d 条 ===' % len(np - lp), flush=True)
for p in sorted(np - lp)[:80]:
    print('NEW:', p, flush=True)

open(r'D:\scan\neon_report\_openapi_v2_prod.json', 'wb').write(raw)
print('saved', flush=True)
