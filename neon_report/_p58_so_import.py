# -*- coding: utf-8 -*-
"""prod_app.js: 定位 so 的 import 来源(vite 形态 import{so}from 或 import * as so)"""
import re, os

here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, '_js', 'prod_app.js'), encoding='utf-8', errors='replace').read()
out = []

# vite/esm 形态: import{...,so,...}from"./xxx.js"
for m in re.finditer(r'import\{[^}]{0,500}?\bso\b[^}]{0,100}\}from"\./([A-Za-z0-9_\-]+\.js)"', src):
    out.append('IMPORT-so: ' + m.group(0)[:400])
# as so 形态
for m in re.finditer(r'import\s+\*\s+as\s+so\s+from\s*"([^"]+)"', src):
    out.append('IMPORT-star-so: ' + m.group(0)[:400])
for m in re.finditer(r'import\{[^}]{0,400}as so[^}]{0,40}\}from"([^"]+)"', src):
    out.append('IMPORT-as-so: ' + m.group(0)[:400])
# export 区找 so 导出: export{...,so,...}
for m in re.finditer(r'export\{[^}]{0,800}\bso\b[^}]{0,200}\}', src):
    out.append('EXPORT-so: ' + m.group(0)[:800])
# 定义: var/const/let so= / function so(
for m in re.finditer(r'(?:var|const|let)\s+so\s*=|function\s+so\s*\(', src):
    i = m.start()
    seg = src[i:i + 600]
    out.append('DEF-so: ' + seg[:550].replace('\n', ' '))

open(os.path.join(here, '_p58_out.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('done lines:', len(out), flush=True)
