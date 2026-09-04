# -*- coding: utf-8 -*-
"""fetch-extension-host-site-sdk-version 调用方与 siteUrl 来源"""
import re

data = open(r'D:\scan\netlify_report\_js\net_app.js', encoding='utf-8', errors='ignore').read()

hits = [m.start() for m in re.finditer(r'fetch-extension-host-site-sdk-version', data)]
print('hits:', len(hits))
for i in hits[:6]:
    seg = data[max(0, i - 2500):i + 1500]
    print('---')
    print(seg.replace('\n', ' ')[-3200:])
    print()
