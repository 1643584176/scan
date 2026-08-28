# -*- coding: utf-8 -*-
"""查看 a669521c 会话(08-28 早上,放弃决定前后)"""
import sys

sys.stdout.reconfigure(encoding='utf-8')
with open(r'D:\scan\skills\non-traditional-vuln-hunting\a669521c_text.txt', encoding='utf-8') as f:
    lines = f.readlines()
print('total segments:', len(lines))
for i, t in enumerate(lines):
    print('%3d: %s' % (i, t.strip()[:420]))
