# -*- coding: utf-8 -*-
"""考古 file_browser_actions 删除端点 + 副本 meta"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

data = open(r'D:\scan\figma_report\_js\figma_app-main.js', encoding='utf-8', errors='replace').read()

# file_browser_actions 模块里删除相关的 API URL
i = data.find('file_browser.file_browser_actions.duplicate_file_error')
print('dup err @', i)
s = max(0, i - 3000)
e = min(len(data), i + 3000)
seg = data[s:e]
# 打印所有 /api/ URL 形态
for m in list(re.finditer(r'`?/api/[a-zA-Z_/${}.\-]*`?', seg))[:30]:
    print(m.group(0)[:150])
print()
# delete/trash 上下文
for kw in ['delete', 'trash']:
    for m in list(re.finditer(kw, seg))[:8]:
        s0 = max(0, m.start() - 150)
        e0 = min(len(seg), m.end() + 200)
        print(f'[{kw}] {seg[s0:e0].replace(chr(10)," ")[:360]}')
        print()
print('ALL DONE')
