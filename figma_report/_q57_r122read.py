# -*- coding: utf-8 -*-
# q57: 读 r122 输出中 A8/A9 用例结果（避免重复打）
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
t = open('_r122_out.txt', encoding='utf-8', errors='replace').read()
lines = t.splitlines()
for i, l in enumerate(lines):
    if 'A8' in l or 'A9' in l or 'B1_del' in l or 'B2_scim' in l or 'B3_email' in l:
        print('\n'.join(lines[i:i+4]))
        print('---')
print('TOTAL LINES:', len(lines))
