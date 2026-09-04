# -*- coding: utf-8 -*-
"""index-LpJ7SKi1.js: 用响应字段名 database_instance_roles 定位 API 方法定义
+ 搜 ag 导出(T 的来源) 与 provisioned 相关对象键
"""
import re, os

here = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(here, '_js', 'prod_chunks', 'index-LpJ7SKi1.js')
src = open(p, encoding='utf-8', errors='replace').read()
out = []

for kw in ['database_instance_roles', 'database_instance', 'databaseInstances', 'provisioned']:
    idxs = [m.start() for m in re.finditer(re.escape(kw), src)]
    out.append('KW %s -> %d' % (kw, len(idxs)))
    for i in idxs[:4]:
        seg = src[max(0, i - 250):i + 400].replace('\n', ' ')
        out.append('  ctx: ' + seg[:600])

# T 导出定义: "ag:" 或 ag= 在 export 区
for m in re.finditer(r'\bag\b', src):
    i = m.start()
    seg = src[max(0, i - 150):i + 150]
    if 'export' in seg or '=' in seg[:80]:
        out.append('--- ag def @%d ---' % i)
        out.append(seg.replace('\n', ' ')[:300])

open(os.path.join(here, '_p51_out.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('done, lines:', len(out), flush=True)
