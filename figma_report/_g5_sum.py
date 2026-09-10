# -*- coding: utf-8 -*-
# g5: 汇总 r196ao/ap/aq 落盘结果(首行+关键字段)
import os, glob, json, io
d = os.path.dirname(os.path.abspath(__file__))
for pref in ['_r196ao_', '_r196ap_', '_r196aq_']:
    files = sorted(glob.glob(os.path.join(d, pref + '*.txt')))
    print('===== %s (%d files) =====' % (pref, len(files)))
    for f in files:
        name = os.path.basename(f)
        if name.endswith('_h1.txt'):
            continue
        c = io.open(f, encoding='utf-8', errors='replace').read()
        head = c.split('\n')
        first = head[0] if head else ''
        body = c[:260].replace('\n', ' ')
        print('%s | %s' % (name, body))
    print()
