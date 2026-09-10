# -*- coding: utf-8 -*-
"""考古2: trash/delete API 端点 (宽松输出)"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

data = open(r'D:\scan\figma_report\_js\figma_app-main.js', encoding='utf-8', errors='replace').read()
n = 0
for m in list(re.finditer(r'trash', data)):
    s = max(0, m.start() - 300)
    e = min(len(data), m.end() + 300)
    seg = data[s:e]
    # 只看包含 API URL 模板或方法调用的
    if re.search(r'/api/[a-z_/${}.\-]+', seg) or '.Ay.del(' in seg or '.Ay.post(' in seg:
        print(f'@{m.start()}: {seg.replace(chr(10)," ")[:560]}')
        print()
        n += 1
        if n > 14:
            break
print('shown', n)
print('ALL DONE')
