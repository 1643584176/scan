# -*- coding: utf-8 -*-
"""h1x56c: 提取 fetch() 全部调用(含模板)+ Backbone url: 定义"""
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
data = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='replace').read()

f1 = re.findall(r'fetch\([`"]([^`"]{1,300})[`"]', data)
print('### fetch literals:', len(f1))
for u in sorted(set(f1)):
    print(' F:', u[:200])

# Backbone/老代码 url 定义
u2 = re.findall(r'url\s*:\s*[`"]([^`"]{1,200})[`"]', data)
print()
print('### url: strings:', len(u2))
for u in sorted(set(u2)):
    print(' U:', u[:200])

# url: function 形态
u3 = re.findall(r'url\s*:\s*function[^}]{0,120}?return\s*[`"]([^`"]{1,200})[`"]', data)
print()
print('### url:function returns:', len(u3))
for u in sorted(set(u3)):
    print(' UF:', u[:200])

# $.ajax / $.get / $.post
u4 = re.findall(r'\$\.(?:ajax|get|post)\([`"]([^`"]{1,200})[`"]', data)
print()
print('### $.ajax etc:', len(u4))
for u in sorted(set(u4)):
    print(' J:', u[:200])
