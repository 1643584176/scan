# -*- coding: utf-8 -*-
"""考古插件发布流程端点: START_PUBLISH 模块的 URL + 创建/发布 plugin 的 API"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

data = open(r'D:\scan\figma_report\_js\figma_app-main.js', encoding='utf-8', errors='replace').read()

# 1115340 上下文 6000 字符内找 Ay URL
seg = data[1115340:1124000]
print('===== publish 模块 URL =====')
for m in re.finditer(r'Ay\.(?:get|post|put|del|patch)\([^)]{0,40}url`[^`]*`[^)]{0,80}\)', seg):
    print(f'@ {1115340+m.start()}: {m.group(0)[:220]}')
    print()
print('===== plugin 创建/发布 URL 全搜 =====')
for pat in [r'url`/api/(?:plugins|widgets)[^`]*`', r'Ay\.(?:get|post|put|del|patch)\([^)]{0,20}/api/(?:plugins|widgets)[^)]{0,100}\)']:
    seen = set()
    for m in re.finditer(pat, data):
        frag = m.group(0)[:120]
        if frag in seen:
            continue
        seen.add(frag)
        s = max(0, m.start() - 100)
        e = min(len(data), m.end() + 100)
        print(f'[{pat[:25]}] @ {m.start()}: {data[s:e][:240]}')
        print()
print('ALL DONE')
