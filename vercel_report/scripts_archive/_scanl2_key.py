# -*- coding: utf-8 -*-
"""从 scanl2 输出提取关键行 (tcp6 表行不打印)"""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')

data = open(r'F:\scan\skills\out\scanl2_scan_local2_guest_20260829_133910.txt', 'rb').read().decode('utf-8', errors='replace')
lines = data.split('\n')
print('total lines:', len(lines))

pat = re.compile(r'PHASE|rows:|target |open:|probe |PTR |candidate|local ips|remote ips|tcp6 rows|ERR|DONE')
for l in lines:
    if pat.search(l):
        print(l[:400])
