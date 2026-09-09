# -*- coding: utf-8 -*-
"""考古: Save local copy / .fig 下载 的官方路径与权限判定"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

data = open(r'D:\scan\figma_report\_js\figma_app-main.js', encoding='utf-8', errors='replace').read()

pats = [
    r'save_local_copy', r'saveLocalCopy', r'save-local-copy', r'local_copy', r'copy_to_local',
    r'save_version', r'\.fig["\']', r'fig_download', r'figdownload', r'download_fig', r'/fig\b',
    r'canExport', r'can_save', r'canDownload', r'downloadVersion',
]
seen = set()
for p in pats:
    for m in list(re.finditer(p, data))[:6]:
        s = max(0, m.start() - 250)
        e = min(len(data), m.end() + 250)
        frag = data[s:e].replace('\n', ' ')
        key = frag[:80]
        if key in seen:
            continue
        seen.add(key)
        print(f'[{p}] @{m.start()}:')
        print('   ', frag[:520])
        print()
print('ALL DONE')
