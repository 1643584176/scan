# -*- coding: utf-8 -*-
"""找 webpack 模块 475861 定义 (follow API)"""
import sys, io, re, glob, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
js_dir = r'D:\scan\figma_report\_js'
for f in glob.glob(os.path.join(js_dir, '*.min.js')):
    data = open(f, encoding='utf-8', errors='ignore').read()
    for m in re.finditer(r'475861\s*:\s*\(', data):
        s = m.start()
        chunk = data[s:s+3000]
        print(f'### {os.path.basename(f)} @{s} ###')
        print(chunk[:2500])
        print()
