# -*- coding: utf-8 -*-
"""考古: @4189762 canExport 消费点的完整 UI 上下文 (定位是哪个按钮/菜单)"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

data = open(r'D:\scan\figma_report\_js\figma_app-main.js', encoding='utf-8', errors='replace').read()
i = data.find('tW=!eB.canExport')
print('@', i)
if i > 0:
    s = max(0, i - 3500)
    e = min(len(data), i + 3500)
    print(data[s:e])
print('ALL DONE')
