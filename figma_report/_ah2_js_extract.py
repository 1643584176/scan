# -*- coding: utf-8 -*-
"""从 figma_app-main.js 提取 admin_requests / addRepeated / ACCOUNT_TYPE_REQUEST 上下文"""
import re, io

p = r'D:\scan\figma_report\_js\figma_app-main.js'
s = open(p, encoding='utf-8', errors='replace').read()
print('js len:', len(s))

out = []

# 1. ACCOUNT_TYPE_REQUEST 出现点上下文
for m in re.finditer(r'ACCOUNT_TYPE_REQUEST', s):
    a, b = max(0, m.start()-300), min(len(s), m.end()+300)
    out.append('===== ACCOUNT_TYPE_REQUEST @%d =====' % m.start())
    out.append(s[a:b])

# 2. addRepeated 定义/调用点
for m in re.finditer(r'addRepeated', s):
    a, b = max(0, m.start()-250), min(len(s), m.end()+250)
    out.append('===== addRepeated @%d =====' % m.start())
    out.append(s[a:b])

# 3. request_types 相关
for m in re.finditer(r'request_types', s):
    a, b = max(0, m.start()-250), min(len(s), m.end()+250)
    out.append('===== request_types @%d =====' % m.start())
    out.append(s[a:b])

io.open(r'D:\scan\figma_report\_ah2_js_ctx.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('written', len(out), 'blocks')
