# -*- coding: utf-8 -*-
"""prod database_instances 路径盲测(401 vs 404 分层, 零破坏只读):
候选: /api/v2/database_instances 及其子资源/相关端点
方法: 无cookie GET(401=路径存在需认证, 404=路由不存在)
      带cookie GET(确认授权层差异)
"""
import http.client, ssl, json, sys, os, time

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_prod import API_HOST, cookie_str

CAND = [
    '/api/v2/database_instances',
    '/api/v2/database-instances',
    '/api/v2/provisioned_instances',
    '/api/v2/projects/database_instances',
    '/api/v2/database_instances/roles',
    '/api/v2/database_instances/catalogs',
    '/api/v2/database_instances/permissions',
    '/api/v2/resolve_lakebase_regions',
    '/api/v2/resolve-lakebase-regions',
    '/api/v2/lakebase/regions',
    '/api/v2/regions/lakebase',
    '/api/v2/provisioned-instances',
    '/api/v2/brickstore',
    '/api/v2/observability/configs',
    '/api/v2/observability/configurations',
    '/api/v2/workspaces',
]

def req(path, with_cookie):
    try:
        conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=20)
        h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
        if with_cookie:
            h['Cookie'] = cookie_str()
        conn.request('GET', path, headers=h)
        r = conn.getresponse()
        raw = r.read().decode('utf-8', 'ignore')
        conn.close()
        return r.status, raw[:300].replace('\n', ' ')
    except Exception as e:
        return -1, 'EXC %s' % e

print('=== 无 cookie(401=路径存在) ===', flush=True)
for p in CAND:
    st, body = req(p, False)
    print('%-55s %s %s' % (p, st, body[:120]), flush=True)

print('=== 带 cookie ===', flush=True)
for p in CAND[:8]:
    st, body = req(p, True)
    print('%-55s %s %s' % (p, st, body[:160]), flush=True)
