# -*- coding: utf-8 -*-
"""扫 net_app.js:proxy 类 functions 的调用方式(URL/参数/方法)"""
import re

data = open(r'D:\scan\netlify_report\_js\net_app.js', encoding='utf-8', errors='ignore').read()

for kw in ['extension-proxy', 'manage-extension-proxy', 'identeer-proxy']:
    hits = [m.start() for m in re.finditer(re.escape(kw), data)]
    print('== %s (%d hits) ==' % (kw, len(hits)))
    for i in hits[:6]:
        print('  ...%s...' % data[max(0, i - 350):i + 350].replace('\n', ' '))
        print()
