# -*- coding: utf-8 -*-
"""研究 __requestId 静态查询机制:用法 + 参数格式"""
import re

d = open('D:/scan/figma_report/_js/figma_app-main.js', 'r', encoding='utf-8', errors='ignore').read()
print('__requestId count:', d.count('__requestId'))
for m in list(re.finditer(r'.{120}__requestId.{120}', d))[:10]:
    print('---', m.group(0).replace('\n', ' ')[:260])
print()
for m in list(re.finditer(r'.{100}requestId.{100}', d))[:10]:
    print('===', m.group(0).replace('\n', ' ')[:240])
