# -*- coding: utf-8 -*-
"""搜 share/export restrict 相关 i18n key 与 UI 文案 (全部 chunk)"""
import sys, io, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

JS = r'D:\scan\figma_report\_js'
files = ['figma_app-main.js'] + [f for f in os.listdir(JS) if f.endswith('.min.js')]
pats = [r'(?:viewer|viewers|export|download|copy)[^"]{0,30}(?:restrict|disable|prevent|limit|off)[^"]{0,60}"',
        r'"[a-z_.]*(?:export|download|copy)_?(?:restrict|limit|prevent)[a-z_.]*"',
        r'"file_access[^"]*"', r'"sharing[^"]*(?:export|download|copy)[^"]*"']
seen = set()
for fn in files:
    try:
        d = open(os.path.join(JS, fn), encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    for p in pats:
        for m in re.finditer(p, d, re.I):
            frag = m.group(0)[:120]
            if frag in seen:
                continue
            seen.add(frag)
            s = max(0, m.start() - 150)
            e = min(len(d), m.end() + 150)
            print(f'{fn} [{frag[:60]}]')
            print(f'   {d[s:e][:330]}')
            print()
print('ALL DONE')
