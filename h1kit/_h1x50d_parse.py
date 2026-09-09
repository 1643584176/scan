# -*- coding: utf-8 -*-
"""确认 InboxState 响应解析 + subjects 来源 + toParam"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
t = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()

# JX 模型完整段(7257k-7266k 范围再细看 parse/toParam/initialize)
seg = t[7257412:7263000]
for m in re.finditer(r'(parse\(|toParam|initialize\(|subjects|url\()', seg):
    j = m.start()
    ctx = seg[max(0, j-200):j+400].replace('\n', ' ')
    print('-' * 60)
    print(m.group(1), '@', 7257412+j, ':', ctx[:500])
