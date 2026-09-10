# -*- coding: utf-8 -*-
# r196m 判读: 全量 dump N 波错误消息(重点: sort_by 白名单 / AdminRequest 查询元组)
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def dump(f, n=4000):
    b = io.open(f, encoding='utf-8', errors='replace').read()
    print('=' * 30, f, len(b))
    print(b[:n])
    print()

for f in ['_r196l_n1.json', '_r196l_n2.json', '_r196l_n3.json']:
    dump(f)
