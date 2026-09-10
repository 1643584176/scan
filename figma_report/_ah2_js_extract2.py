# -*- coding: utf-8 -*-
"""挖 JS:SchemaValidator 定义 / requestPermissionLevel 用法 / queryString 的 zod 描述"""
import re, io

p = r'D:\scan\figma_report\_js\figma_app-main.js'
s = open(p, encoding='utf-8', errors='replace').read()

out = []
pats = [
    (r'AdminRequestsDashboardViewSchemaValidator', 400),
    (r'AdminRequestsListSchemaValidator', 400),
    (r'AdminRequestCountsSchemaValidator', 400),
    (r'requestPermissionLevel', 300),
    (r'request_permission_levels', 250),
]
seen = set()
for pat, w in pats:
    out.append('########## PATTERN: %s ##########' % pat)
    for m in re.finditer(pat, s):
        a, b = max(0, m.start()-w), min(len(s), m.end()+w)
        key = s[a:b][:100]
        if key in seen:
            continue
        seen.add(key)
        out.append('===== @%d =====' % m.start())
        out.append(s[a:b])

io.open(r'D:\scan\figma_report\_ah2_js_ctx2.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('written', len(out), 'lines')
