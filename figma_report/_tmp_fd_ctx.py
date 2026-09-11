# -*- coding: utf-8 -*-
"""抽: q3 ctx(调用点) + q1_paths 映射 + z24/z26 diff 脚本 + g1_scripts 线索"""
import os, io

FIG = r'D:/scan/figma_report'

def dump(fn, maxlen=6000):
    p = os.path.join(FIG, fn)
    if not os.path.exists(p):
        print('MISSING', fn); return
    txt = io.open(p, encoding='utf-8', errors='ignore').read()
    print('=' * 35, fn, '(%d chars)' % len(txt))
    print(txt[:maxlen])
    if len(txt) > maxlen:
        print('...[截断]')
    print()

dump('_q3_ctx_out.txt', 5000)
dump('_figma_z24_diff.py', 3500)
dump('_figma_z26_fv.py', 3500)

print('=' * 35, '_q1_paths.json file_diff 行')
p = os.path.join(FIG, '_q1_paths.json')
txt = io.open(p, encoding='utf-8', errors='ignore').read()
i = txt.find('file_diff')
while i >= 0:
    print('...%s...' % txt[max(0, i - 120):i + 200].replace('\n', ' '))
    i = txt.find('file_diff', i + 1)

print()
print('=' * 35, '_g1_scripts.txt from_file_version_id 行')
p = os.path.join(FIG, '_g1_scripts.txt')
if os.path.exists(p):
    txt = io.open(p, encoding='utf-8', errors='ignore').read()
    for i, ln in enumerate(txt.split('\n')):
        if 'from_file_version_id' in ln or 'file_diff' in ln:
            print('%4d| %s' % (i + 1, ln.strip()[:180]))
