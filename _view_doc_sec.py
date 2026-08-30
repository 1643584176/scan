# -*- coding: utf-8 -*-
"""查看 create-a-named-sandbox 文档关键区段"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

p = r'C:\Users\lbb.LAPTOP-LU4P5L6T\.qoder\cache\projects\scan-dcb95ef8\agent-tools\cecd10e6\008f9507.txt'
txt = open(p, encoding='utf-8', errors='replace').read()
lines = txt.splitlines()

print('===== 25-110 (请求体参数定义区) =====')
for i in range(25, 110):
    print('%4d: %s' % (i, lines[i][:250]))

print()
print('===== 390-480 (请求示例 + 响应示例) =====')
for i in range(390, 480):
    print('%4d: %s' % (i, lines[i][:250]))
