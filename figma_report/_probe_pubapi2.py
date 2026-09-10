# -*- coding: utf-8 -*-
"""考古 195149 模块剩余端点 (uninstall/publishers role 常量) + community URL 全集"""
import sys, io, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

JS = r'D:\scan\figma_report\_js'
main = os.path.join(JS, 'figma_app-main.js')
data = open(main, encoding='utf-8', errors='replace').read()

# 找 195149 模块定义尾部 (下一个模块 id 前) - 模块很大, 找模块内所有 Ay.URL
i = data.find('195149(e,t,r){')
if i < 0:
    i = data.find('195149(e,t,r)')
print(f'module 195149 at {i}')
seg = data[i:i+20000]
# 段内所有 URL 模板
for m in re.finditer(r'url`[^`]*`', seg):
    print(f'URL@ {m.start()}: {m.group(0)[:160]}')
print()
# 段内角色常量 (kM)
for m in list(re.finditer(r'kM\s*=\s*\{[^}]+\}', seg))[:3]:
    print(f'kM: {m.group(0)[:200]}')
print()
# publishers 相关全部调用点 (main)
print('===== publishers 调用 (main) =====')
for m in list(re.finditer(r'publishers[^`"]{0,60}', data))[:10]:
    s = max(0, m.start() - 120)
    e = min(len(data), m.end() + 80)
    print(f'@ {m.start()}: {data[s:e][:250]}')
    print()
print('ALL DONE')
