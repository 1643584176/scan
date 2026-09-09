# -*- coding: utf-8 -*-
"""考古 voting_sessions 创建参数 (1158557 附近 createVotingSession body)"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

data = open(r'D:\scan\figma_report\_js\figma_app-main.js', encoding='utf-8', errors='replace').read()
seg = data[1155000:1159500]
# 找 C 函数 (createVotingSession action) 的参数构造
print(seg[:4500])
print('ALL DONE')
