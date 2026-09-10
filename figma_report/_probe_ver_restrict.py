# -*- coding: utf-8 -*-
"""考古 viewer_export_restricted 的 UI 语义 (设置弹窗/分享开关文案)"""
import sys, io, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

JS = r'D:\scan\figma_report\_js'
files = ['figma_app-main.js'] + [f for f in os.listdir(JS) if f.endswith('.min.js')]
for fn in files:
    try:
        d = open(os.path.join(JS, fn), encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    for kw in ['viewer_export_restricted', 'export_restricted', 'viewers_can', 'can_copy', 'restrict']:
        for m in list(re.finditer(kw, d))[:5]:
            s = max(0, m.start() - 200)
            e = min(len(d), m.end() + 250)
            print(f'=== {fn} [{kw}] @ {m.start()}:')
            print(f'   {d[s:e][:450]}')
            print()
print('ALL DONE')
