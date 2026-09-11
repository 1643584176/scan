# -*- coding: utf-8 -*-
# q70: 读 r229 V6 / r231 参数名变异 / r232 / r195b camel引号 / r132 遍历 的结果
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def dump(fn, keys=None, maxl=45, ctx=2):
    print(f'\n######## {fn}')
    try:
        lines = open(fn, encoding='utf-8', errors='replace').read().splitlines()
    except Exception as e:
        print(' ERR', e); return
    if keys is None:
        for l in lines[:maxl]:
            print(' ', l[:165])
    else:
        for i, l in enumerate(lines):
            if any(k in l for k in keys):
                print('>>', '\n   '.join(x[:170] for x in lines[i:i+ctx]))

dump('_r229_out.txt', ['V6', 'Plan_ID', 'PLAN_ID', 'V7', 'V8'], ctx=2)
print('...')
dump('_r231_out.txt', ['参数名', 'Plan_', 'planId', 'camel', 'P1', 'P2', 'P3'], ctx=2)
print('...')
dump('_r232_out.txt', None, 30)
print('...')
dump('_r195b_out.txt', ['H1', 'camel', 'seenResourceIds'], ctx=2)
print('...')
dump('_r132_out.txt', ['plan_id', 'planId', "for k"], ctx=2)
print('DONE q70')
