# -*- coding: utf-8 -*-
"""追 S,R,D 变量定义 (R=approveButton)"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

fp = r'D:\scan\figma_report\_js\9668-5317375f131d42d8.min.js'
data = open(fp, encoding='utf-8', errors='ignore').read()

# 在 pos ~50000-51289 区间找 S/R/D 的赋值
seg = data[47000:51290]
for m in re.finditer(r'(?:S|R|D)\s*=', seg):
    s = max(0, m.start() - 200)
    print(f'--- pos {47000+m.start()} ---')
    print(seg[s:m.end() + 250].replace('\n', ' ')[:380])
    print()
