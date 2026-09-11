# -*- coding: utf-8 -*-
# r197d 分析2: JSON 结构级逐文件逐字段比对(仅剥离 realtime_token)
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def body_json(p):
    d = open(p, 'rb').read().split(b'\n', 1)
    return json.loads(d[1].decode('utf-8'))

def strip(f):
    return {k: v for k, v in f.items() if k != 'realtime_token'}

variants = ['C1_base', 'C1r_replay', 'C2_ref', 'C3_arith', 'C4_frag',
            'C6a_notexist', 'C6b_small', 'C10_arith0', 'C10b_arith1',
            'C11_frag', 'C12_quote']
base = body_json('_r197_%s.txt' % 'C1_base')
bfl = [strip(x) for x in base['meta']['files']]
top = {k: v for k, v in base.items() if k not in ('meta',)}
bmeta = {k: v for k, v in base['meta'].items() if k != 'files'}
print('C1 top keys:', list(top.keys()), 'meta keys:', list(bmeta.keys()))
print('C1 files:', [(x.get('key'), x.get('name'), x.get('folder_id')) for x in bfl])
for v in variants:
    j = body_json('_r197_%s.txt' % v)
    fl = [strip(x) for x in j['meta']['files']]
    order_same = (fl == bfl)
    set_same = (sorted(fl, key=lambda x: str(x.get('key'))) == sorted(bfl, key=lambda x: str(x.get('key'))))
    t2 = {k: x for k, x in j.items() if k not in ('meta',)}
    m2 = {k: x for k, x in j['meta'].items() if k != 'files'}
    print('%-14s n=%d order_same=%s set_same=%s top=%s meta=%s' % (
        v, len(fl), order_same, set_same, t2 == top, m2 == bmeta), flush=True)
    if not set_same:
        for a, b in zip(sorted(fl, key=lambda x: str(x.get('key'))),
                        sorted(bfl, key=lambda x: str(x.get('key')))):
            if a != b:
                ka = set(a) | set(b)
                for k in sorted(ka):
                    if a.get(k) != b.get(k):
                        print('    field %r: base=%r vs %r' % (k, b.get(k), a.get(k)), flush=True)
                break
