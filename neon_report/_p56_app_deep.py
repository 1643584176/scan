# -*- coding: utf-8 -*-
"""prod_app.js: 搜 provisioned instance API 方法/响应字段/URL"""
import re, os

here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, '_js', 'prod_app.js'), encoding='utf-8', errors='replace').read()
out = []

for kw in ['listProvisionedInstanceRoles', 'createProvisionedInstanceRole',
           'database_instance_roles', 'provisioned_instance', 'database_instance',
           'provisioned-instances', 'useCurrentProvisionedInstance']:
    idxs = [m.start() for m in re.finditer(re.escape(kw), src)]
    out.append('KW %s -> %d' % (kw, len(idxs)))
    for i in idxs[:6]:
        seg = src[max(0, i - 300):i + 400].replace('\n', ' ')
        out.append('  ctx: ' + seg[:650])

open(os.path.join(here, '_p56_out.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('done lines:', len(out), flush=True)
