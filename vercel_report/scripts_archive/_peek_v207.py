# -*- coding: utf-8 -*-
import sys
p = r'C:\Users\tndc2\.qoder\cache\projects\scan-72ece876\agent-tools\9aa693e0\e2ed552c.txt'
d = open(p, encoding='utf-8', errors='replace').read()
i = d.find('REPLAY-newts')
cnt = 0
while i >= 0 and cnt < 6:
    print(d[max(0, i - 120):i + 350])
    print('----')
    i = d.find('REPLAY-newts', i + 1)
    cnt += 1
i = d.find('CONN 3 req')
if i >= 0:
    print('CONN3 CTX:')
    print(d[max(0, i - 80):i + 1500])
else:
    print('no conn3')
