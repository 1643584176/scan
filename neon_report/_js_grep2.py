# -*- coding: utf-8 -*-
"""搜 bundle:org header 名/拦截器构造/createProject mutation"""
import re
txt = open(r'D:\scan\neon_report\_js\app.js', encoding='utf-8').read()

patterns = ['x-neon', 'X-Neon', 'neon-org', 'organization-id', 'orgId:', 'org_id:', 'headers:{', 'headers:{...', 'organization_id']
for kw in patterns:
    hits = [m.start() for m in re.finditer(re.escape(kw), txt, re.I)]
    print('== %s : %d hits' % (kw, len(hits)))
    for i in hits[:4]:
        print('  CTX:', txt[max(0, i - 200):i + 200].replace('\n', ' ')[:380])

# createProject mutation 精确定位
for m in re.finditer(r'createProject\s*[:(]', txt):
    i = m.start()
    print('\nCP CTX:', txt[max(0, i - 150):i + 400].replace('\n', ' ')[:520])
