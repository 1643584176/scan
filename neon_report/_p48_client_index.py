# -*- coding: utf-8 -*-
"""下载 index-LpJ7SKi1.js -> 搜 provisioned instance API 端点 URL"""
import http.client, ssl, re, os

ctx = ssl.create_default_context()
here = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(here, '_js', 'prod_chunks', 'index-LpJ7SKi1.js')

if not os.path.exists(p):
    conn = http.client.HTTPSConnection('dfv3qgd2ykmrx.cloudfront.net', context=ctx, timeout=60)
    conn.request('GET', '/assets/index-LpJ7SKi1.js', headers={'User-Agent': 'Mozilla/5.0'})
    r = conn.getresponse()
    raw = r.read()
    conn.close()
    open(p, 'wb').write(raw)
    print('downloaded', len(raw), flush=True)
src = open(p, encoding='utf-8', errors='replace').read()
print('size:', len(src), flush=True)

for kw in ['listProvisionedInstanceRoles', 'createProvisionedInstanceRole',
           'updateProvisionedInstanceRole', 'dropProvisionedInstanceRole',
           'listProvisionedInstanceCatalogs', 'deleteProvisionedInstanceCatalog',
           'createProvisionedInstanceCatalog', 'listProvisionedInstances',
           'createProvisionedInstance', 'deleteProvisionedInstance',
           'ProvisionedInstance', 'provisioned_instances']:
    idxs = [m.start() for m in re.finditer(re.escape(kw), src)]
    for i in idxs[:2]:
        seg = src[max(0, i - 300):i + 400].replace('\n', ' ')
        print('### %s (%d)' % (kw, len(idxs)), flush=True)
        print(seg[:700], flush=True)
