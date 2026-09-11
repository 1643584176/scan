# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
txt = open('_r216_out.txt', encoding='utf-8', errors='replace').read()
i = txt.find('E 段')
if i >= 0:
    print(txt[i:i+1600])
else:
    # 找 E1
    j = txt.find('[E1]')
    print(txt[max(0, j-200):j+1600] if j >= 0 else '未找到 E 段/E1')
