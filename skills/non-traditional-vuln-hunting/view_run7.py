# -*- coding: utf-8 -*-
"""查看 pidfd_run8.log 关键输出"""
import sys, re

sys.stdout.reconfigure(encoding='utf-8')
raw = open(r'D:\scan\skills\non-traditional-vuln-hunting\pidfd_run8.log', encoding='utf-8').read()
# 找 trigger 行
for m in re.finditer(r'"trigger (\d+): (\d+) (.*?)"', raw):
    print('trigger:', m.group(1), m.group(2), m.group(3)[:80])
print('=== data blocks ===')
outs = re.findall(r'"data":"(.*?)"', raw)
print('count:', len(outs))
for i, o in enumerate(outs):
    t = o.encode().decode('unicode_escape', errors='replace')
    print('--- block %d ---' % i)
    print(t[:3000])
    if len(t) > 3000:
        print('...[truncated %d]' % len(t))
