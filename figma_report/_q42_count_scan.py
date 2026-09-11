# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
f = 'Figma-SQL注入-r212-213-盲区深打-结论-2026-09-11.md'
txt = open(f, encoding='utf-8').read()
for i, line in enumerate(txt.splitlines(), 1):
    if '39' in line or '发' in line and ('共' in line or '合计' in line or '请求' in line):
        print(i, '|', line)
print('---')
print('总行数:', len(txt.splitlines()))
