# -*- coding: utf-8 -*-
"""提取 rotate_credentials 完整逻辑 + expose_owner_credentials_to_pat 使用点 + GET /database 上下文"""
import re

d = open(r'D:\scan\netlify_report\_js\net_app.js', encoding='utf-8', errors='ignore').read()

def ctx(pat, back=500, fwd=600, label=None, maxhits=4):
    print(f'==== {label or pat} ====')
    hits = 0
    for m in re.finditer(pat, d):
        i = m.start()
        print(d[max(0, i - back):i + fwd].replace('\n', ' ')[:back + fwd])
        print('----')
        hits += 1
        if hits >= maxhits:
            break
    if hits == 0:
        print('(no hit)')

ctx(r'expose_owner_credentials_to_pat', 800, 400, 'EXPOSE-OWNER-SETTING', 6)
ctx(r'Failed to rotate credentials', 2500, 200, 'ROTATE-FULL', 1)
