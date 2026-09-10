# -*- coding: utf-8 -*-
import io, re
js = io.open('_js/figma_app-main.js', encoding='utf-8', errors='replace').read()
print('== sortOrder ctx')
for m in list(re.finditer(r'.{90}sortOrder.{110}', js))[:26]:
    print('SO>', repr(m.group(0))[:230])
print('== paginatedRecentFiles ctx')
for m in list(re.finditer(r'.{100}paginatedRecentFiles.{130}', js))[:10]:
    print('PRF>', repr(m.group(0))[:250])
print('== orderBy ctx')
for m in list(re.finditer(r'.{70}orderBy.{90}', js))[:20]:
    print('OB>', repr(m.group(0))[:180])
print('DONE')
