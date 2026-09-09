# -*- coding: utf-8 -*-
"""考古: 文件删除/trash 的 API 端点"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

data = open(r'D:\scan\figma_report\_js\figma_app-main.js', encoding='utf-8', errors='replace').read()
for kw in ['trash', 'move_to_trash', 'delete_file', 'deleteFile', '/api/trash', 'file_delete']:
    ms = list(re.finditer(re.escape(kw), data))
    print(f'===== [{kw}] x{len(ms)} =====')
    for m in ms[:6]:
        s = max(0, m.start() - 160)
        e = min(len(data), m.end() + 240)
        seg = data[s:e].replace('\n', ' ')
        if '/api/' in seg or 'url`' in seg or '.Ay.' in seg:
            print(f'@{m.start()}: {seg[:420]}')
            print()
print('ALL DONE')
