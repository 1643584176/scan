# -*- coding: utf-8 -*-
"""考古 1146271 保存版本调用上下文: 找 916129.J 的调用参数与 URL"""
import sys, io, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

JS = r'D:\scan\figma_report\_js'
main = os.path.join(JS, 'figma_app-main.js')
data = open(main, encoding='utf-8', errors='replace').read()

# 1146271 前后大窗口
print('===== @1146271 前后 4000 =====')
print(data[1142271:1150271])
print('ALL DONE')
