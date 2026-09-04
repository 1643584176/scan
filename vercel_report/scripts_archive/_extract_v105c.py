# -*- coding: utf-8 -*-
"""找 v105 输出中的 [p3 file] 段"""
import re, io

txt = io.open('_run_v105_out.txt', encoding='utf-8', errors='replace').read()
# 直接搜索 p3 关键字
idxs = [m.start() for m in re.finditer(r'\[p3 file\]', txt)]
print('p3 file markers:', len(idxs))
if idxs:
    k = idxs[-1]
    print(txt[k:k + 4000])
