# -*- coding: utf-8 -*-
"""在文件中搜索关键字, 打印上下文行"""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')

path, kws = sys.argv[1], sys.argv[2:]
data = open(path, encoding='utf-8', errors='replace').read()
lines = data.splitlines()
for i, ln in enumerate(lines):
    if any(k.lower() in ln.lower() for k in kws):
        lo = max(0, i - 2)
        hi = min(len(lines), i + 3)
        print('--- line %d-%d ---' % (lo, hi))
        for j in range(lo, hi):
            print('%d| %s' % (j, lines[j][:300]))
