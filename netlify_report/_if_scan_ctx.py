# -*- coding: utf-8 -*-
"""bundle 调用上下文:identeer-proxy 全部用法 / fetch-site-configuration 参数 / agent-runner-file-delete 参数"""
import re

data = open(r'D:\scan\netlify_report\_js\net_app.js', encoding='utf-8', errors='ignore').read()

for kw in ['identeer-proxy', 'fetch-site-configuration', 'agent-runner-file-delete']:
    hits = [m.start() for m in re.finditer(re.escape(kw), data)]
    print('== %s (%d hits) ==' % (kw, len(hits)))
    for i in hits[:5]:
        print('  ...%s...' % data[max(0, i - 700):i + 700].replace('\n', ' '))
        print()
