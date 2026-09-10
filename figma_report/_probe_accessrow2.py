# -*- coding: utf-8 -*-
"""考古 file_access_row 组件全貌: N(e) 返回 true 时渲染的文案/开关"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

data = open(r'D:\scan\figma_report\_js\figma_app-main.js', encoding='utf-8', errors='replace').read()

# 找到 N 函数定义 (file_access_row 内 function N)
i = data.find('function N(e){return!!(!e.canEdit&&e.viewer_export_restricted&&e.link_access===d.PQ.INHERIT)')
print('N def @', i)
if i > 0:
    # 往前找组件起始 (前一个 "file_access_row" 或模块头)
    s = max(0, i - 4000)
    print(data[s:i + 2500])
print('ALL DONE')
