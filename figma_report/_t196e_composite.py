# -*- coding: utf-8 -*-
import io, re
js = io.open('_js/figma_app-main.js', encoding='utf-8', errors='replace').read()
print('== compositeParentResourceId logic ctx')
hits = list(re.finditer(r'.{130}compositeParentResourceId.{150}', js))
print('total', len(hits))
n = 0
for m in hits:
    s = m.group(0)
    if 'o("' in s and 'View"' in s:
        continue  # 跳过 View 注册行
    n += 1
    print('CP>', repr(s)[:280])
    if n >= 22:
        break
print('== composite make funcs')
for pat in [r'.{100}CompositeParent.{110}', r'.{100}compositeId.{110}', r'.{90}getCompositeParent.{110}']:
    for m in list(re.finditer(pat, js))[:6]:
        print('FN>', repr(m.group(0))[:230])
print('DONE')
