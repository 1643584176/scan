# -*- coding: utf-8 -*-
"""git 函数挂载点:github-proxied 上下文 + 各 host 探测"""
import re, sys, http.client, ssl, gzip, brotli

for fn in [r'D:\scan\netlify_report\_js\net_actions.js', r'D:\scan\netlify_report\_js\net_app.js', r'D:\scan\netlify_report\_js\net_lib.js']:
    data = open(fn, encoding='utf-8', errors='ignore').read()
    for key in ['github-proxied', 'proxied', '/.netlify/functions/git']:
        n = 0
        for m in re.finditer(re.escape(key), data):
            s = max(0, m.start() - 600)
            e = min(len(data), m.end() + 600)
            print('#' * 20, fn.split('\\')[-1], key, 'hit', n)
            try:
                print(data[s:e].replace('\n', ' '))
            except Exception:
                print(data[s:e].encode('utf-8', 'ignore').decode('utf-8', 'ignore'))
            print('-' * 50)
            n += 1
            if n >= 3:
                break
