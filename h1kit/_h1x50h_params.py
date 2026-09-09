# -*- coding: utf-8 -*-
"""h1x50h: 提取完整 viewParams + defaults 全列表(判断可注入参数全集)"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
t = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()

# defaults() 与 viewParams getter 全文
for m in re.finditer(r'get viewParams', t):
    j = m.start()
    seg = t[j:j+1200]
    print('=' * 20, 'viewParams @', j)
    print(seg[:1200])
    break

# defaults 段:往回找 defaults(){ 并输出
i = 7257412
seg = t[i:i+2000]
m = re.search(r'defaults\(\)\{', seg)
if m:
    j = i + m.start()
    print('=' * 20, 'defaults @', j)
    print(t[j:j+900])
