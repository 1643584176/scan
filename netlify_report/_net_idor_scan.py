# -*- coding: utf-8 -*-
"""Netlify 交叉 IDOR 扫描:B token -> A 资源(OpenAPI GET 端点全表)
只读操作,无副作用"""
import http.client, ssl, gzip, brotli, json, sys, re
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B

SITE_A = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
ACC_ID_A = '6a979dd2ae93f47d55b62897'
ACC_SLUG_A = '1643584176'
DEPLOY_A = '6a97c9e3083c963fd210b895'
ctx = ssl.create_default_context()

def api(token, path):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=15)
    h = {'User-Agent': 'netlify-cli/17.0.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Authorization': 'Bearer ' + token}
    try:
        conn.request('GET', path, headers=h)
        r = conn.getresponse()
        raw = r.read()
        enc = r.getheader('Content-Encoding')
        if enc == 'br':
            raw = brotli.decompress(raw)
        elif enc == 'gzip':
            raw = gzip.decompress(raw)
        st = r.status
        conn.close()
        return st, raw
    except Exception as e:
        return 'ERR', str(e)[:60].encode()

# 手工挑选可能带敏感数据的 GET 端点,替换资源 id
tpl = [
    '/api/v1/sites/{site_id}/files',
    '/api/v1/sites/{site_id}/files/',
    '/api/v1/sites/{site_id}/forms',
    '/api/v1/sites/{site_id}/submissions',
    '/api/v1/sites/{site_id}/snippets',
    '/api/v1/sites/{site_id}/build_hooks',
    '/api/v1/sites/{site_id}/hooks',
    '/api/v1/sites/{site_id}/assets',
    '/api/v1/sites/{site_id}/dns',
    '/api/v1/sites/{site_id}/service-instances',
    '/api/v1/sites/{site_id}/services/',
    '/api/v1/sites/{site_id}/ssl',
    '/api/v1/sites/{site_id}/traffic_splits',
    '/api/v1/sites/{site_id}/deployed-branches',
    '/api/v1/sites/{site_id}/database',
    '/api/v1/sites/{site_id}/database/branches',
    '/api/v1/sites/{site_id}/database/snapshots',
    '/api/v1/sites/{site_id}/database/migrations',
    '/api/v1/sites/{site_id}/database/compute/settings',
    '/api/v1/sites/{site_id}/plugin_runs/latest?packages=',
    '/api/v1/sites/{site_id}/functions',
    '/api/v1/sites/{site_id}/deploys',
    '/api/v1/sites/{site_id}/dev_servers',
    '/api/v1/sites/{site_id}/agent_runner_hooks',
    '/api/v1/sites/{site_id}/ai-gateway/token',
    '/api/v1/sites/{site_id}/metadata',
    '/api/v1/sites/{site_id}/env',
    '/api/v1/accounts/{account_id}/env',
    '/api/v1/accounts/{account_id}/audit',
    '/api/v1/accounts/{account_id}/ai-gateway/token',
    '/api/v1/deploys/{deploy_id}',
    '/api/v1/deploy_keys',
    '/api/v1/dns_zones',
    '/api/v1/hooks?site_id={site_id}',
    '/api/v1/forms/',
    '/api/v1/oauth/tickets/',
    '/{account_slug}/members',
    '/{account_slug}/sites',
    '/{account_slug}/members/',
    '/api/v1/agent_runners?account_id={account_id}&site_id={site_id}',
    '/api/v1/ai-gateway/providers',
    '/api/v1/user',
    '/api/v1/billing/payment_methods',
]
interesting = []
for t in tpl:
    p = t.replace('{site_id}', SITE_A).replace('{account_id}', ACC_ID_A) \
         .replace('{account_slug}', ACC_SLUG_A).replace('{deploy_id}', DEPLOY_A)
    st, raw = api(TOKEN_B, p)
    body = raw[:180].decode('utf-8', 'replace').replace('\n', ' ')
    # 关注点:200(泄漏)/403(存在但拒绝)/400/500 都打印;401/404 隐藏跳过
    if st in (200, 403, 400, 500, 422):
        print('[!!] %-70s %s %s' % (p, st, body))
    else:
        print('    %-70s %s' % (p, st))
