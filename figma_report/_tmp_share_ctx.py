# -*- coding: utf-8 -*-
"""1. 9300 模块内 u 的消费点 2. ai_assistant_sharing 用法 3. privacyMode 转换流程"""
import os, re

JS = r'F:/scan/figma_report/_js'
ALL = {}
for fn in os.listdir(JS):
    if fn.endswith('.js'):
        try:
            ALL[fn] = open(os.path.join(JS, fn), encoding='utf-8', errors='ignore').read()
        except Exception:
            pass

# 1. 9300 中 function u 之后的使用(在 426104 模块内继续搜 u( 调用)
c9300 = ALL.get('9300-41a18cb0f8ba922b.min.js', '')
print('=== 9300: u 函数后的同模块使用 ===')
i0 = c9300.find('function u(e){')
if i0 > 0:
    seg = c9300[i0:i0 + 3000]
    for m in re.finditer(r'[^a-zA-Z](u)\(', seg):
        i = m.start()
        print('   ...', seg[max(0, i - 80):i + 120].replace('\n', ' ')[:200])
print()

print('=== 9300 模块导出与相邻模块(u 被 import 的痕迹) ===')
for m in list(re.finditer(r'426104[^;]{0,50}', c9300))[:6]:
    print('   ', m.group(0)[:150])

print()
print('=== 全目录 ai_assistant_sharing ===')
for fn, c in ALL.items():
    for m in re.finditer(r'[^,;{}]{0,150}ai_assistant_sharing[^,;{}]{0,150}', c):
        print(f'-- {fn}')
        print('   ', m.group(0)[:300].replace('\n', ' '))

print()
print('=== privacyMode 赋值/转换(shared/user/file) ===')
for fn, c in ALL.items():
    for m in re.finditer(r'[^,;{}]{0,120}(?:privacyMode\s*[:=]|privacy_mode|setPrivacy)[^,;{}]{0,140}', c):
        g = m.group(0)
        if 'user' in g or 'file' in g or 'shared' in g or 'overrid' in g.lower():
            print(f'-- {fn}: {g[:260].replace(chr(10), " ")}')
