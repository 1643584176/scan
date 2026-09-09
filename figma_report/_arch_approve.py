# -*- coding: utf-8 -*-
"""挖 approveButton 的启用条件与 publishers 语义"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

fp = r'D:\scan\figma_report\_js\9668-5317375f131d42d8.min.js'
data = open(fp, encoding='utf-8', errors='ignore').read()

# approveButton 变量赋值上下文 (在 BasicResourceHeader 使用前)
for m in re.finditer(r'approveButton', data):
    s = max(0, m.start() - 300)
    ctx = data[s:m.start() + 100]
    # 找定义处: 含 approve/Button 赋值
    if re.search(r'approveButton[:=]|approveButton\s*[,}]', ctx):
        print(f'=== pos {m.start()} ===')
        print(ctx[-350:].replace('\n', ' '))
        print()

# pending 列表从哪来 + approve mutation 的 enabled 条件
for m in re.finditer(r'pending', data):
    s = max(0, m.start() - 150)
    ctx = data[s:m.start() + 150]
    if re.search(r'enabled|isPending|\.pending\s*=|pending\?', ctx):
        print(f'--- pending ctx pos {m.start()} ---')
        print(ctx.replace('\n', ' ')[:300])
        print()
