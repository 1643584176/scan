# -*- coding: utf-8 -*-
"""script 6(early.js)全文 dump 到文件 + 935 中 u 函数/chunk 映射"""
import re

c = open('D:/scan/figma_report/_js/app_file.html', 'r', encoding='utf-8', errors='ignore').read()
scripts = re.findall(r'<script(?![^>]*src)[^>]*>(.*?)</script>', c, re.S)
s6 = scripts[6]
open('D:/scan/figma_report/_js/early.js.txt', 'w', encoding='utf-8').write(s6)
print('saved early.js.txt len', len(s6))

# 935 中的 chunk 映射(webpack5: {935:"hash", ...} 无引号 key)
d = open('D:/scan/figma_report/_js/935-431f89677a39072c.min.js', 'r', encoding='utf-8', errors='ignore').read()
for m in re.finditer(r'\{[0-9]+:"[0-9a-f]{6,40}"(?:,[0-9]+:"[0-9a-f]{6,40}"){2,}\}', d):
    print('935 chunkmap:', m.group(0)[:600])
# 找 .u= 函数
for m in list(re.finditer(r'\.u=[^,;]{0,200}', d))[:3]:
    print('u fn:', m.group(0)[:220])
for m in list(re.finditer(r'\.u\s*=\s*function[^}]{0,200}', d))[:3]:
    print('u fn2:', m.group(0)[:220])
