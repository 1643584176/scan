# -*- coding: utf-8 -*-
"""考古 /api/widgets/v2/versions 调用上下文 + widget 相关端点"""
import sys, io, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

JS = r'D:\scan\figma_report\_js'
main = os.path.join(JS, 'figma_app-main.js')
data = open(main, encoding='utf-8', errors='replace').read()

# 668375 前后大窗口
print('===== @668375 前后 3500 =====')
print(data[668175:672000])
print()
print('===== widgets API 端点全搜 =====')
for pat in [r'Ay\.\w+\([^)]{0,30}url`[^`]*widgets[^`]*`[^)]{0,60}\)', r'[/]api/widgets[^"\x60]{0,80}']:
    seen = set()
    for m in list(re.finditer(pat, data)):
        frag = m.group(0)[:120]
        if frag in seen:
            continue
        seen.add(frag)
        s = max(0, m.start() - 150)
        e = min(len(data), m.end() + 120)
        print(f'PAT@ {m.start()}: {data[s:e][:300]}')
        print()
print('ALL DONE')
