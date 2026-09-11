# -*- coding: utf-8 -*-
# q65: 读 r111e/r142/r209m2/r226 输出 + r111d 端点定义——列/排序参数的历史细节
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def dump(fn, keys=None, maxl=40, ctx=2):
    print(f'\n######## {fn}')
    try:
        lines = open(fn, encoding='utf-8', errors='replace').read().splitlines()
    except Exception as e:
        print(' ERR', e); return
    if keys is None:
        for l in lines[:maxl]:
            print(' ', l[:160])
    else:
        for i, l in enumerate(lines):
            if any(k in l for k in keys):
                print('>>', '\n   '.join(x[:170] for x in lines[i:i+ctx]))

dump('_figma_r111d.py', maxl=30)
print('...')
dump('_r111e_out.txt', keys=None, maxl=45)
print('...')
dump('_r142_out.txt', keys=['column', 'before'], ctx=3, maxl=0)
print('...')
dump('_r209m2_out.txt', keys=['A1', 'A4', 'A5'], ctx=3)
print('...')
dump('_r226_out.txt', keys=['S1', 'S2', 'S3'], ctx=3)
print('DONE q65')
