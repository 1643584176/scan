# -*- coding: utf-8 -*-
"""解析已抓社区 HTML: 找资源 URL 形态与内嵌数据"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

t = open(r'D:\scan\figma_report\_comm_plugins.html', encoding='utf-8', errors='replace').read()
# 各种 URL 形态
for pat in [r'href="[^"]*community/plugin[^"]*"', r'href="[^"]*community/widget[^"]*"',
            r'community[^"\x60]{0,80}(?:plugin|widget)[^"\x60]{0,60}']:
    hits = list(dict.fromkeys(re.findall(pat, t)))[:5]
    print(f'== {pat[:20]}:')
    for h in hits:
        print(f'   {h[:200]}')
# __NEXT_DATA__ / __figma 数据?
for kw in ['__NEXT_DATA__', '__FIGMA_DATA__', 'application/ld+json', 'resourceId', 'pluginId']:
    i = t.find(kw)
    print(f'== {kw} @ {i}')
    if i >= 0:
        print(f'   {t[i:i+400]}')
# 数字 id 附近上下文
m = re.search(r'"id":\s*"?(\d{10,30})', t)
print('first numeric id ctx:', t[max(0, m.start()-150):m.end()+150] if m else 'none')
print('ALL DONE')
