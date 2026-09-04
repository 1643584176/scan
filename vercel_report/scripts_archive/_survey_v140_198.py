# -*- coding: utf-8 -*-
"""survey v140-v198 probe payload 目的, 输出一行摘要"""
import glob

for n in range(140, 199):
    pats = glob.glob(r'D:\scan\skills\non-traditional-vuln-hunting\vda%d_probe_guest.py' % n)
    if not pats:
        continue
    lines = open(pats[0], encoding='utf-8', errors='replace').read().splitlines()
    doc = []
    for l in lines[1:10]:
        s = l.strip().strip('"')
        if s.startswith('v1') or s.startswith('#') or s.startswith('1)') or s.startswith('2)') \
                or s.startswith('3)') or s.startswith('4)') or s.startswith('5)') or s.startswith('6)') \
                or s.startswith('7)') or s.startswith('8)') or s.startswith('9)') or s.startswith('0)') \
                or '通道' in s or s.startswith('输出'):
            doc.append(s)
    print('v%d: %s' % (n, ' | '.join(doc)[:160]))
