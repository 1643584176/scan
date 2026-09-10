# -*- coding: utf-8 -*-
"""h1x21: 提取 BetterReportDuplicates + ExactText 完整字符串 query 到文件"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

t = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()

out = []
for name in ['BetterReportDuplicates', 'BetterReportDuplicatesExactText', 'BetterReportDuplicatesExactTextFeatureToggled']:
    i = t.find('query ' + name)
    if i == -1:
        out.append(f'{name}: NF\n'); continue
    seg = t[max(0, i-300):i+8000]
    m = re.search(r'"(.*?query ' + name + r'.*?)"', seg, re.S)
    if m:
        s = m.group(1).replace('\\n', '\n')
        out.append(f'===== {name} (len {len(s)}) =====\n{s}\n')
    else:
        out.append(f'{name}: no string\n')

open(r'D:\scan\h1kit\_h1x21_out.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('written', sum(len(x) for x in out), 'chars')
