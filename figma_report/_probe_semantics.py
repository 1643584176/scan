# -*- coding: utf-8 -*-
"""考古 file/claim + hub_files copy + collections + weave 调用上下文"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

data = open(r'D:\scan\figma_report\_js\figma_app-main.js', encoding='utf-8', errors='replace').read()
for kw in [r'url`[^`]*file/claim[^`]*`', r'url`[^`]*hub_files[^`]*`', r'url`[^`]*collections[^`]*`',
           r'url`[^`]*weave[^`]*`', r'url`[^`]*voting_sessions[^`]*`', r'url`[^`]*multiplayer[^`]*copy[^`]*`']:
    print(f'===== {kw[:35]} =====')
    n = 0
    for m in re.finditer(kw, data):
        s = max(0, m.start() - 300)
        e = min(len(data), m.end() + 300)
        print(f'@ {m.start()}: {data[s:e][:600]}')
        print()
        n += 1
        if n >= 3:
            break
print('ALL DONE')
