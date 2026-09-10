# -*- coding: utf-8 -*-
"""考古: 分享弹窗 viewer_export_restricted 开关的渲染/切换 API"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

data = open(r'D:\scan\figma_report\_js\figma_app-main.js', encoding='utf-8', errors='replace').read()

# 1. file_permissions_modal 的 i18n key 清单 (export/download/copy/restrict)
for pat in [r'file_permissions_modal\.[a-z_.0-9]+', r'file_access_row\.[a-z_.0-9]+']:
    keys = sorted(set(re.findall(pat, data)))
    print(f'===== {pat} keys ({len(keys)}) =====')
    for k in keys:
        if any(w in k for w in ['export', 'download', 'copy', 'restrict', 'viewer', 'save', 'duplicate']):
            print('  ', k)
    print()

# 2. 开关切换调用 (含 viewerExportRestricted / exportRestricted 的 UI 交互)
for kw in ['viewerExportRestricted', 'exportRestricted', 'canExport', 'isExportRestricted', 'setViewerExport']:
    ms = list(re.finditer(re.escape(kw), data))
    print(f'===== [{kw}] x{len(ms)} =====')
    for m in ms[:6]:
        s = max(0, m.start() - 220)
        e = min(len(data), m.end() + 220)
        print(f'@{m.start()}: {data[s:e].replace(chr(10)," ")[:460]}')
        print()
print('ALL DONE')
