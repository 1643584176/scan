# -*- coding: utf-8 -*-
"""考古: @4189762 菜单项列表, 找 tY/tW(canExport) 控制的项"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

data = open(r'D:\scan\figma_report\_js\figma_app-main.js', encoding='utf-8', errors='replace').read()
i = data.find('tW=!eB.canExport')
s = i + 3500
e = min(len(data), i + 12000)
seg = data[s:e]
print(seg)
print('ALL DONE')
