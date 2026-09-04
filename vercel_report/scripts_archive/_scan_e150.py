# -*- coding: utf-8 -*-
"""GBK 读取 e1507845_text.txt，提取 celld/CreateSnapshot 相关上下文"""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')

data = open(r'F:\scan\skills\non-traditional-vuln-hunting\e1507845_text.txt', 'rb').read()
txt = data.decode('gbk', errors='replace')
lines = txt.splitlines()
print('total lines:', len(lines))

# 找 celld 相关行
hits = []
for i, l in enumerate(lines):
    if re.search(r'celld|CreateSnapshot|base_url|baseUrl|23456|vsock|V25|V26|V27|V28|V29', l, re.I):
        hits.append((i, l))
print('hits:', len(hits))
# 打印关键行（含上下文）
for i, l in hits:
    print('%4d: %s' % (i, l[:250]))
