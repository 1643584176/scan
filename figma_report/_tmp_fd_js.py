# -*- coding: utf-8 -*-
"""找 checkpoint_diff 的 JS 调用形态 + FK2 的 checkpoint id 来源"""
import os, io, re

FIG = r'D:/scan/figma_report'
JSD = os.path.join(FIG, '_js')
PATS = ['checkpoint_diff', 'checkpointDiff', 'file_diff', 'fileDiff']

print('===== A. _js 目录扫描 =====')
hits = 0
for root, dirs, files in os.walk(JSD):
    for fn in files:
        fp = os.path.join(root, fn)
        try:
            txt = io.open(fp, encoding='utf-8', errors='ignore').read()
        except Exception:
            continue
        for p in PATS:
            c = txt.count(p)
            if c:
                hits += 1
                i = txt.find(p)
                seg = txt[max(0, i - 300):i + 500].replace('\n', ' ')
                print('%-50s [%s] x%d' % (os.path.relpath(fp, FIG), p, c))
                print('   ...%s...' % seg[:650])
                print()
                break
if not hits:
    print('(无命中)')

print('===== B. 顶层 json 里的 checkpoint / 版本对象 =====')
for fn in os.listdir(FIG):
    if not fn.endswith('.json'):
        continue
    fp = os.path.join(FIG, fn)
    try:
        txt = io.open(fp, encoding='utf-8', errors='ignore').read()
    except Exception:
        continue
    c1, c2 = txt.count('checkpoint'), txt.count('laF5guxdhRzBcWmVwfKJ4e')
    if c1 or c2:
        print('%-50s checkpoint=%d fk2=%d' % (fn, c1, c2))

print()
print('===== C. 源码汇总文档里的 checkpoint/file_diff =====')
p = os.path.join(FIG, 'Figma-SQL请求解析源码汇总-2026-09-10.md')
if os.path.exists(p):
    txt = io.open(p, encoding='utf-8', errors='ignore').read()
    for i, ln in enumerate(txt.split('\n')):
        if 'checkpoint' in ln or 'file_diff' in ln or 'diff_version' in ln:
            print('%4d| %s' % (i + 1, ln.strip()[:190]))
