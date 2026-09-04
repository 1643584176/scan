# -*- coding: utf-8 -*-
"""挖 extension-proxy / extension 内部函数调用形态"""
import re

for fn in [r'D:\scan\netlify_report\_js\net_app.js', r'D:\scan\netlify_report\_js\net_actions.js',
           r'D:\scan\netlify_report\_js\net_ui.js', r'D:\scan\netlify_report\_js\net_lib.js']:
    data = open(fn, encoding='utf-8', errors='ignore').read()
    for key in ['extension-proxy', 'extension_proxy', 'extensionProxy', '/functions/extension',
                'fetch-extension', 'extension-host']:
        n = 0
        for m in re.finditer(re.escape(key), data):
            s = max(0, m.start() - 800)
            e = min(len(data), m.end() + 800)
            print('#' * 25, fn.split('\\')[-1], '|', key, '| hit', n)
            seg = data[s:e].replace('\n', ' ')
            print(seg[:1500])
            print('-' * 60)
            n += 1
            if n >= 4:
                break
