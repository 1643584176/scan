# -*- coding: utf-8 -*-
"""侦察: file_diff/checkpoint_diff 的全部既有情报"""
import os, io

ROOTS = [r'D:/scan/figma_report', r'D:/scan/经验/全局经验/SQL注入经验库']
PATS = ['file_diff', 'checkpoint', 'from_file_version_id', 'fromFileVersionId',
        'migration_version', 'nodes_to_diff', 'diff_version']

def scan_dir(path, exts):
    for fn in sorted(os.listdir(path)):
        if not fn.lower().endswith(exts):
            continue
        fp = os.path.join(path, fn)
        if not os.path.isfile(fp):
            continue
        try:
            txt = io.open(fp, encoding='utf-8', errors='ignore').read()
        except Exception:
            continue
        hits = {}
        for p in PATS:
            n = txt.count(p)
            if n:
                hits[p] = n
        if hits:
            print('%-60s %s' % (fn, hits))

for root in ROOTS:
    print('#' * 25, root)
    scan_dir(root, ('.py', '.md'))
    print()
