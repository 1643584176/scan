# -*- coding: utf-8 -*-
"""考古 984002 版本动作模块定义 -> 保存/恢复版本 REST URL"""
import sys, io, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

JS = r'D:\scan\figma_report\_js'
main = os.path.join(JS, 'figma_app-main.js')
data = open(main, encoding='utf-8', errors='replace').read()

# 模块定义 984002: (格式变体)
for pat in [r'984002:\s*\(', r'984002:\s*function', r',984002:\s*\(', r'984002:\s*e\s*=>']:
    for m in list(re.finditer(pat, data))[:2]:
        s = m.start()
        print(f'DEF@ {s}: {data[s:s+2500]}')
        print('======')
print('ALL DONE')
