# -*- coding: utf-8 -*-
"""考古: viewerExportRestrictedAt 消费点 + 导出限制的 UI 行为"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

data = open(r'D:\scan\figma_report\_js\figma_app-main.js', encoding='utf-8', errors='replace').read()

# 1. viewerExportRestrictedAt 所有出现
print('===== viewerExportRestrictedAt 出现点 =====')
for m in list(re.finditer(r'viewerExportRestrictedAt', data))[:20]:
    s = max(0, m.start() - 300)
    e = min(len(data), m.end() + 300)
    print('@%d:' % m.start())
    print('   ', data[s:e].replace('\n', ' ')[:600])
    print()

# 2. 导出限制相关: 找 canExport / exportRestricted / saveLocalCopy 权限检查
print('===== export 权限检查 =====')
for kw in ['canExport', 'exportRestricted', 'canSaveLocalCopy', 'restrictExport']:
    for m in list(re.finditer(kw, data))[:8]:
        s = max(0, m.start() - 200)
        e = min(len(data), m.end() + 200)
        print(f'[{kw}] @{m.start()}:')
        print('   ', data[s:e].replace('\n', ' ')[:420])
        print()
print('ALL DONE')
