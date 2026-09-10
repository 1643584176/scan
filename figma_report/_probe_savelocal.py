# -*- coding: utf-8 -*-
"""考古: 网页编辑器 File > Save a local copy 的 action 实现与端点 (全 chunk)"""
import sys, io, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

JS = r'D:\scan\figma_report\_js'
files = ['figma_app-main.js'] + sorted(f for f in os.listdir(JS) if f.endswith('.min.js'))

# 1. 先定位 UI 菜单文案/i18n key
pats = [
    r'save[a-z_]*local[a-z_]*copy[a-z_.]*', r'save_local_copy', r'localCopy',
    r'save_a_copy', r'save-a-copy', r'save_copy', r'file_download', r'download_local',
    r'menu.*save.*copy', r'save.*copy.*menu',
]
print('===== 1. 菜单/i18n 定位 =====')
seen = {}
for fn in files:
    try:
        d = open(os.path.join(JS, fn), encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    for p in pats:
        for m in list(re.finditer(p, d, re.I))[:6]:
            frag = d[max(0, m.start()-120):m.end()+200].replace('\n', ' ')[:340]
            k = (fn, frag[:60])
            if k in seen:
                continue
            seen[k] = 1
            print(f'--- {fn} [{m.group(0)[:40]}]')
            print(f'    {frag}')
            print()
print('ALL DONE')
