# -*- coding: utf-8 -*-
"""ctx12: J 调用点上下文深挖 + fileVersion 来源 + nodes_to_diff/migration_version 线索"""
import os, io, re

JS = r'D:\scan\figma_report\_js'
main = os.path.join(JS, 'figma_app-main.js')
t = io.open(main, encoding='utf-8', errors='ignore').read()
print('main len:', len(t))

# 1) J 调用点上下文（pos 2587384 附近）
pos = 2587384
print('=' * 20, 'J callsite ctx [pos-2600, pos+1800]')
print(t[max(0, pos - 2600):pos + 1800])
print()

# 2) fileVersion 出现（最多 12 个）
print('=' * 20, 'fileVersion hits')
i = 0; n = 0
while True:
    i = t.find('fileVersion', i)
    if i < 0: break
    n += 1
    if n <= 12:
        print('--- hit', n, 'pos', i, '::', t[max(0, i - 120):i + 180].replace('\n', ' ')[:300])
    i += 11
print('   total fileVersion:', n)

# 3) nodes_to_diff
print('=' * 20, 'nodes_to_diff hits')
i = 0; n = 0
while True:
    i = t.find('nodes_to_diff', i)
    if i < 0: break
    n += 1
    if n <= 10:
        print('--- hit', n, 'pos', i, '::', t[max(0, i - 150):i + 200].replace('\n', ' ')[:350])
    i += 13
print('   total:', n)

# 4) migration_version
print('=' * 20, 'migration_version hits')
i = 0; n = 0
while True:
    i = t.find('migration_version', i)
    if i < 0: break
    n += 1
    if n <= 10:
        print('--- hit', n, 'pos', i, '::', t[max(0, i - 150):i + 200].replace('\n', ' ')[:350])
    i += 17
print('   total:', n)
print('DONE12')
