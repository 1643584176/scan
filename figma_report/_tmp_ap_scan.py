# -*- coding: utf-8 -*-
# 归集 r196ap 输出
import io, glob, os
d = os.path.dirname(os.path.abspath(__file__))
fs = sorted(glob.glob(os.path.join(d, '_r196ap_*.txt')))
print('COUNT:', len(fs))
for f in fs:
    bn = os.path.basename(f)
    txt = io.open(f, encoding='utf-8', errors='replace').read()
    first = txt.split('\n', 1)
    st = first[0] if first else '?'
    body = (first[1] if len(first) > 1 else '').replace('\n', ' ')[:240]
    print('%s :: %s :: %s' % (bn, st, body))
