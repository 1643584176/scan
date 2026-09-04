# -*- coding: utf-8 -*-
"""Netlify:spark-proxy knowledge 调用完整上下文"""
import os, re

jsdir = r'D:\scan\netlify_report\_js'
for f in sorted(os.listdir(jsdir)):
    if not f.endswith('.js'):
        continue
    txt = open(os.path.join(jsdir, f), encoding='utf-8', errors='ignore').read()
    for m in re.finditer(r'spark-proxy/api/v1/knowledge', txt):
        i = m.start()
        ctx = txt[max(0, i - 5000): i + 2000]
        # 找 knowledge 调用的函数定义头
        # 找 scopes 的构造
        for sm in re.finditer(r'scopes', ctx):
            j = sm.start()
            print('[%s] scopes ctx:' % f.replace('net_', '').replace('.js', ''))
            print('  ', ctx[max(0, j - 400): j + 400].replace('\n', ' ')[:800])
            print()
        break
