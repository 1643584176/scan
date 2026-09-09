# -*- coding: utf-8 -*-
"""考古 community plugin/widget 发布管理端点全集: publishers/roles/versions URL"""
import sys, io, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

JS = r'D:\scan\figma_report\_js'
main = os.path.join(JS, 'figma_app-main.js')
data = open(main, encoding='utf-8', errors='replace').read()

# publishers 全部调用 + 模块 export 区域 672622 后 3000
print('===== @672622 后 4000 =====')
print(data[672622:677000])
print('ALL DONE')
