# -*- coding: utf-8 -*-
"""index-LpJ7SKi1.js 深度: ProvisionedInstance API 方法定义定位
方法命名规律: 上一步 Roles chunk 调 T.listProvisionedInstanceRoles
-> 搜方法名定义位置, 提取方法体内 URL 字面量
"""
import re, os

here = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(here, '_js', 'prod_chunks', 'index-LpJ7SKi1.js')
src = open(p, encoding='utf-8', errors='replace').read()
out = []

# 1. 方法名列表(从 UI chunk 调用推断 + 命名规律盲扩)
methods = [
    'listProvisionedInstanceRoles', 'createProvisionedInstanceRole',
    'updateProvisionedInstanceRole', 'dropProvisionedInstanceRole',
    'listProvisionedInstanceCatalogs', 'createProvisionedInstanceCatalog',
    'updateProvisionedInstanceCatalog', 'deleteProvisionedInstanceCatalog',
    'listProvisionedInstancePermissions', 'grantProvisionedInstancePermission',
    'revokeProvisionedInstancePermission', 'listProvisionedInstances',
    'createProvisionedInstance', 'deleteProvisionedInstance',
    'getProvisionedInstance', 'restartProvisionedInstance',
    'provisionedInstances', 'provisioned-instances',
    'database_instances', 'databaseInstances',
    'lakebase', 'Lakebase',
]
found = {}
for mth in methods:
    idxs = [m.start() for m in re.finditer(re.escape(mth), src)]
    if idxs:
        found[mth] = idxs
        out.append('KW %s -> %d' % (mth, len(idxs)))
        for i in idxs[:3]:
            seg = src[max(0, i - 120):i + 260].replace('\n', ' ')
            out.append('   ctx: ' + seg[:360])

# 2. URL 字面量中含 instance 的路径
urls = set()
for m in re.finditer(r'["\'`](/(?:api|v1|v2|ajax-api)[^"\'`]{0,120}instance[^"\'`]{0,80})["\'`]', src):
    urls.add(m.group(1))
for m in re.finditer(r'["\'`](/(?:api|v1|v2|ajax-api)[^"\'`]{0,120}lakebase[^"\'`]{0,80})["\'`]', src):
    urls.add(m.group(1))
out.append('=== instance/lakebase URL 字面量 ===')
for u in sorted(urls):
    out.append(u)

# 3. instance_id / instanceId 附近的 URL 拼接(模板字符串 /api/xxx/${...})
segs = []
for m in re.finditer(r'instanceId', src):
    i = m.start()
    seg = src[max(0, i - 300):i + 200]
    if '/api' in seg or 'api/' in seg or '${' in seg:
        segs.append(seg.replace('\n', ' ')[:500])
out.append('=== instanceId 附近含 api 的上下文(%d) ===' % len(segs))
for s in segs[:12]:
    out.append(s)

p2 = os.path.join(here, '_p49_out.txt')
open(p2, 'w', encoding='utf-8').write('\n'.join(out))
print('done, lines:', len(out), flush=True)
