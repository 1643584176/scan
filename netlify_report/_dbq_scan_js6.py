# -*- coding: utf-8 -*-
"""扫 net_app.js:settings 与 snapshot 的写操作(POST/PATCH 路径与方法)"""
import re

data = open(r'D:\scan\netlify_report\_js\net_app.js', encoding='utf-8', errors='ignore').read()

for kw in ['expose_owner_credentials_to_pat', 'database/snapshot', 'database/snapshots', 'database/settings',
           'database/compute', 'deploy-and-rollback']:
    hits = [m.start() for m in re.finditer(re.escape(kw), data)]
    print('== %s (%d) ==' % (kw, len(hits)))
    for i in hits[:3]:
        print('  ...%s...' % data[max(0, i - 400):i + 400].replace('\n', ' '))
        print()
