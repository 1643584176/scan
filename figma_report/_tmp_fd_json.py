# -*- coding: utf-8 -*-
"""检查 _r196* / 旧 json 里的 checkpoint 上下文 - 找真实 checkpoint id"""
import os, io, json

FIG = r'D:/scan/figma_report'
FILES = ['_r196f_h4.json', '_r196i_k3.json', '_r196j_l1.json', '_q1_paths.json',
         '_r111c_neg1.json', '_r36_copy.json', '_r41_copy.json', '_p112_state_A.json']

for fn in FILES:
    p = os.path.join(FIG, fn)
    if not os.path.exists(p):
        print('MISSING', fn)
        continue
    txt = io.open(p, encoding='utf-8', errors='ignore').read()
    print('=' * 30, fn, len(txt))
    print('HEAD:', txt[:300].replace('\n', ' '))
    i = txt.find('checkpoint')
    n = 0
    while i >= 0 and n < 3:
        seg = txt[max(0, i - 250):i + 400].replace('\n', ' ')
        print('  ctx%d: ...%s...' % (n + 1, seg))
        i = txt.find('checkpoint', i + 1)
        n += 1
    print()
