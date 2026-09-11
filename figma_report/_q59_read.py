# -*- coding: utf-8 -*-
# q59: 读 r214a A9(全角数字) / r227 T13a 结果 + r225 超长位 确认
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
for fn, keys in [('_r214a_out.txt', ['A9']), ('_r227_out.txt', ['T13a']), ('_r225_out.txt', ['Q1', 'q1'])]:
    try:
        t = open(fn, encoding='utf-8', errors='replace').read()
    except Exception as e:
        print(fn, 'ERR', e); continue
    lines = t.splitlines()
    print(f'### {fn}')
    for i, l in enumerate(lines):
        if any(k in l for k in keys):
            print('\n'.join(lines[i:i+3]))
            print('---')
print('DONE q59')
