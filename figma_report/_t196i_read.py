# -*- coding: utf-8 -*-
import io, re
for f in ['_r196i_k2.json', '_r196i_k3.json', '_r196i_k4.json']:
    b = io.open(f, encoding='utf-8', errors='replace').read()
    ti = b.find('trashedResources')
    print('=====', f, 'len', len(b))
    if ti >= 0:
        print('QRY>', repr(b[max(0, ti - 60):ti + 420])[:480])
    # initial 数据结构样本
    ii = b.find('"initial":{')
    if ii >= 0:
        print('INIT>', repr(b[ii:ii + 700])[:760])
    print()
print('DONE')
