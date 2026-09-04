# -*- coding: utf-8 -*-
"""搜 ProvisionedInstance API 方法定义位置与端点路径:
- listProvisionedInstanceRoles/Catalogs, createProvisionedInstanceRole 等定义(在 prod_app.js 还是共享 chunk)
- 方法体里的 URL
"""
import re, os, glob

here = os.path.dirname(os.path.abspath(__file__))
cands = []
for root in [os.path.join(here, '_js'), os.path.join(here, '_js', 'prod_chunks')]:
    for fn in os.listdir(root):
        if not fn.endswith('.js'):
            continue
        p = os.path.join(root, fn)
        try:
            s = open(p, encoding='utf-8', errors='replace').read()
        except Exception:
            continue
        for kw in ['listProvisionedInstanceRoles', 'createProvisionedInstanceRole',
                   'listProvisionedInstanceCatalogs', 'deleteProvisionedInstanceCatalog',
                   'listProvisionedInstances', 'createProvisionedInstance',
                   'provisioned_instances', 'database_instances']:
            i = s.find(kw)
            if i >= 0:
                print('### %s | %s' % (fn, kw), flush=True)
                print(s[max(0, i - 200):i + 500].replace('\n', ' ')[:700], flush=True)
                cands.append((fn, kw))
                break
print('done, hits:', cands, flush=True)
