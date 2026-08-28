# -*- coding: utf-8 -*-
"""解析 pidfd_run13.log 关键输出"""
import re, sys
sys.stdout.reconfigure(encoding='utf-8')
raw = open(r'D:\scan\skills\non-traditional-vuln-hunting\pidfd_run13.log', encoding='utf-8', errors='replace').read()

print("=== triggers ===")
for m in re.finditer(r'trig (\d+\.\d+) (\w+): (\d+)', raw):
    print(m.group(0)[:120])

print("\n=== guest ACCEPT/SEND ===")
for pat in ['ACCEPT srcfd=9 ->', 'ACCEPTED fd=15 total=', 'SEND ', 'POST-SEND', 'LISTEN THREAD', 'PHASE3 done']:
    for m in re.finditer(re.escape(pat), raw):
        i = m.start()
        print(raw[i:i+200].replace('\n', ' ')[:200])
    print('---')
