# -*- coding: utf-8 -*-
"""关键 chunk 宽搜: provisioned instance / permission / catalog / observability config 相关端点上下文"""
import re, os

here = os.path.dirname(os.path.abspath(__file__))
d = os.path.join(here, '_js', 'prod_chunks')

def ctx_of(fn, kws, before=250, after=400, maxn=4):
    p = os.path.join(d, fn)
    if not os.path.exists(p):
        return
    src = open(p, encoding='utf-8', errors='replace').read()
    for kw in kws:
        idxs = [m.start() for m in re.finditer(re.escape(kw), src)]
        if idxs:
            print('### %s | %s -> %d' % (fn, kw, len(idxs)), flush=True)
        for i in idxs[:maxn]:
            seg = src[max(0, i - before):i + after].replace('\n', ' ')
            print('  ', seg[:600], flush=True)

# Provisioned Instances: 找 API 路径特征
ctx_of('ProvisionedInstancesItemRoles-BFeEbS-M.js', ['/api', 'instance_id', 'instanceId', 'role', 'grant', 'permission'], 200, 350, 3)
ctx_of('ProvisionedInstancesItemPermissions-D0kxYUw1.js', ['/api', 'permission', 'principal', 'grant'], 200, 350, 3)
ctx_of('ProvisionedInstancesItemCatalogs-0DPn8ML0.js', ['/api', 'catalog'], 200, 350, 3)
ctx_of('CreateOrEditProvisionedInstanceModal-RFT4nmPC.js', ['/api', 'create', 'provision'], 200, 350, 3)
ctx_of('ProvisionedInstancesList-CTp5c_4X.js', ['/api', 'list', 'provision'], 200, 350, 3)
