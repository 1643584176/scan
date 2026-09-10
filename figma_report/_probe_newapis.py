# -*- coding: utf-8 -*-
"""考古 block / resource_uses / save / bulk_favorite 调用上下文"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

data = open(r'D:\scan\figma_report\_js\figma_app-main.js', encoding='utf-8', errors='replace').read()

for kw in [r'url`[^`]*/block[^`]*`', r'url`[^`]*resource_uses[^`]*`', r'url`[^`]*/save[^`]*`',
           r'url`[^`]*bulk_favorite[^`]*`', r'url`[^`]*generate_handle[^`]*`', r'url`[^`]*related_content[^`]*`',
           r'url`[^`]*resource_scope_settings[^`]*`', r'url`[^`]*planless_favorited[^`]*`']:
    print(f'===== {kw[:30]} =====')
    n = 0
    for m in re.finditer(kw, data):
        s = max(0, m.start() - 250)
        e = min(len(data), m.end() + 250)
        print(f'@ {m.start()}: {data[s:e][:500]}')
        print()
        n += 1
        if n >= 2:
            break
print('ALL DONE')
