# -*- coding: utf-8 -*-
"""prod_app.js: 定位 so 的 API client 定义(listDatabaseInstances 方法体 + so 实例化)"""
import re, os

here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, '_js', 'prod_app.js'), encoding='utf-8', errors='replace').read()
out = []

for kw in ['listDatabaseInstances', 'getUpgradeToAutoscalingStatus', 'listProvisionedInstanceRoles']:
    idxs = [m.start() for m in re.finditer(re.escape(kw), src)]
    out.append('KW %s -> %d' % (kw, len(idxs)))
    for i in idxs[:4]:
        seg = src[max(0, i - 800):i + 400].replace('\n', ' ')
        out.append('  ctx: ' + seg[:1150])

open(os.path.join(here, '_p57_out.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('done lines:', len(out), flush=True)
