# -*- coding: utf-8 -*-
"""考古: 文件删除 action 的 API 调用 (找 U1 定义与 delete/trash URL)"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

data = open(r'D:\scan\figma_report\_js\figma_app-main.js', encoding='utf-8', errors='replace').read()

# 1. U1 action 定义: 搜 "U1:" 导出附近或 filesByKey action
for kw in ['U1({filesByKey', 'U1:', 'filesByKey:{[', 'fileKeys:{[', 'files/trash', 'trash_files', 'file/trash',
           'delete_files', 'files.delete', 'removeFile', 'files/${', '/api/files/${']:
    ms = list(re.finditer(re.escape(kw), data))
    print(f'===== [{kw}] x{len(ms)} =====')
    for m in ms[:5]:
        s = max(0, m.start() - 200)
        e = min(len(data), m.end() + 400)
        print(f'@{m.start()}: {data[s:e].replace(chr(10)," ")[:600]}')
        print()
print('ALL DONE')
