# -*- coding: utf-8 -*-
# meta 瞬态字段定位: C1 vs C1r_replay
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def bj(p):
    d = open(p, 'rb').read().split(b'\n', 1)
    return json.loads(d[1].decode('utf-8'))

a = bj('_r197_C1_base.txt')['meta']
b = bj('_r197_C1r_replay.txt')['meta']

def walk(x, y, path='meta'):
    if isinstance(x, dict) and isinstance(y, dict):
        for k in x:
            walk(x[k], y.get(k), path + '/' + k)
    elif isinstance(x, list) and isinstance(y, list):
        for i, (u, v) in enumerate(zip(x, y)):
            walk(u, v, path + '[%d]' % i)
    else:
        if x != y:
            print(path, '::', repr(x)[:120], '->', repr(y)[:120], flush=True)

walk(a, b)
print('OK')
