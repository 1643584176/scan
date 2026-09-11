# -*- coding: utf-8 -*-
"""挖 JS: checkpoint_diff 命中上下文 + migration_version/diff_version 全部命中"""
import os, io

JS = r'D:\scan\figma_report\_js'
terms = ['checkpoint_diff', 'migration_version', 'migrationVersion', 'file_diff']
for f in sorted(os.listdir(JS)):
    if not f.endswith('.js'):
        continue
    try:
        t = io.open(os.path.join(JS, f), encoding='utf-8', errors='ignore').read()
    except Exception:
        continue
    for term in terms:
        i = 0
        n = 0
        while True:
            i = t.find(term, i)
            if i < 0:
                break
            n += 1
            seg = t[max(0, i - 600):i + 800]
            print('=' * 18, f, '|', term, '| hit', n, '| pos', i)
            print(seg.replace('\n', ' ')[:1400])
            print()
            i += len(term)
            if n > 12:
                print('... (more hits truncated)')
                break
print('SCAN DONE')
