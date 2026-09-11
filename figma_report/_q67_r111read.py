# -*- coding: utf-8 -*-
# q67: 找 r111 系列输出 + 读白名单/兄弟端点结果
import sys, io, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print('===== r111 输出文件 =====')
for fn in sorted(glob.glob('_r111*') + glob.glob('_r112*') + glob.glob('_r113*')):
    print(' ', fn)

def dump(fn, keys=None, maxl=55, ctx=2):
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
                print('>>', '\n   '.join(x[:172] for x in lines[i:i+ctx]))

dump('_r111c_out.txt', None, 60)
print('...')
dump('_r111b_out.txt', ['F_', 'ps_neg', 'ps_huge', 'ancestors', 'contributors'], ctx=2)
print('DONE q67')
