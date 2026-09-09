# -*- coding: utf-8 -*-
"""考古 file_access_row UI 逻辑: viewer export restrict 的展示/切换条件 + 保存端点"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

data = open(r'D:\scan\figma_report\_js\figma_app-main.js', encoding='utf-8', errors='replace').read()

# @4635521 上下文大窗口
print('===== @4635521 前后 6000 =====')
print(data[4633000:4640000])
print('ALL DONE')
