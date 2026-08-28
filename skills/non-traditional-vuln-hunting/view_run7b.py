# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
raw = open(r'D:\scan\skills\non-traditional-vuln-hunting\pidfd_run10.log', encoding='utf-8').read()
import re
for m in re.finditer(r'trigger (\d+): (\d+)', raw):
    print('trigger:', m.group(1), m.group(2))
print('PHASE3 done:', 'PHASE3 done' in raw)
print('ACCEPT count:', raw.count('ACCEPT'))
print('PEEK count:', raw.count('PEEK'))
i = raw.find('PHASE3 start')
print('--- after PHASE3 start ---')
print(raw[i:i+800])
print('--- last 400 chars ---')
print(raw[-400:])
