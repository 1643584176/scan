# -*- coding: utf-8 -*-
"""main JS 中 916129 全部出现上下文 (找 chunk map / 懒加载定义)"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

data = open(r'D:\scan\figma_report\_js\figma_app-main.js', encoding='utf-8', errors='replace').read()
pos = 0
while True:
    i = data.find('916129', pos)
    if i < 0:
        break
    s = max(0, i - 200)
    e = min(len(data), i + 250)
    print(f'@ {i}:')
    print(f'   ...{data[s:e]}...')
    print()
    pos = i + 6
print('ALL DONE')
