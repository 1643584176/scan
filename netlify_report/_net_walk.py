# -*- coding: utf-8 -*-
"""Netlify:OpenAPI 180 端点遍历(带认证,只读优先,记录非预期响应)"""
import http.client, ssl, gzip, brotli, sys, json, re, yaml
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import AUTH_HEADER

ctx = ssl.create_default_context()

def api(path, method='GET', body=None):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=20)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip', 'Accept': 'application/json',
         'Authorization': AUTH_HEADER}
    if body is not None:
        h['Content-Type'] = 'application/json'
        body = json.dumps(body).encode()
    conn.request(method, path, body=body, headers=h)
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

# 加载 swagger
sw = yaml.safe_load(open(r'D:\scan\netlify_report\_openapi\swagger.yml', encoding='utf-8'))
paths = sw.get('paths', {})

SITE = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ACC = '1643584176'
USER = '6a979dd2ae93f47d55b62895'

# 替换路径参数为真实值;只跑 GET(避免副作用)
results = []
for p, methods in paths.items():
    if 'get' not in methods:
        continue
    pp = p
    for k, v in [('site_id', SITE), ('account_id', ACC), ('account_slug', ACC),
                 ('user_id', USER), ('deploy_id', 'none'), ('function_name', 'x'),
                 ('build_id', 'none'), ('form_id', 'none'), ('submission_id', 'none'),
                 ('domain', 'example.com'), ('dns_zone_id', 'none'), ('snippet_id', 'none'),
                 ('file_path', 'index.html'), ('path', 'index.html'), ('name', 'x'),
                 ('key', 'x'), ('id', 'none'), ('slug', 'x'), ('token', 'x'),
                 ('owner_id', ACC), ('service_slug', 'x'), ('service_id', 'x'),
                 ('ticket_id', 'none'), ('payment_method_id', 'none'), ('plan', 'x'),
                 ('installation_id', 'none'), ('integration_id', 'none'), ('integration_slug', 'x'),
                 ('integration_installation_id', 'none'), ('task_id', 'none'), ('asset_id', 'none'),
                 ('link_id', 'none'), ('member_id', 'none'), ('invite_id', 'none'),
                 ('environment_id', 'none'), ('variable_id', 'none'), ('edge_function_id', 'none'),
                 ('split_id', 'none'), ('framework', 'x'), ('branch', 'x'), ('traffic_domain', 'x'),
                 ('domain_id', 'none'), ('zone_id', 'none'), ('record_id', 'none')]:
        pp = pp.replace('{%s}' % k, v)
        pp = pp.replace('{%s}' % k.upper(), v)
    # 补 query 参数:required 的常见参数
    qs = []
    for pname in methods['get'].get('parameters', []):
        if pname.get('in') == 'query' and pname.get('required'):
            qs.append('%s=x' % pname['name'])
    if qs:
        sep = '&' if '?' in pp else '?'
        pp = pp + sep + '&'.join(qs)
    try:
        s, raw = api(pp)
        body = raw[:100].decode('utf-8', 'ignore').replace('\n', ' ')
        if s not in (200, 401, 404, 400, 422):
            results.append((s, 'GET', pp, body))
            print('UNEXPECTED %d GET %s  %s' % (s, pp[:90], body[:90]))
        elif s == 200 and len(raw) > 5:
            print('200 GET %s  %s' % (pp[:90], body[:90]))
    except Exception as e:
        print('ERR GET %s %s' % (pp[:90], str(e)[:40]))

print()
print('unexpected count:', len(results))
