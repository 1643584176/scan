# -*- coding: utf-8 -*-
"""dump admin_requests 模块全文区域 (2719500-2728000)"""
import io

p = r'D:\scan\figma_report\_js\figma_app-main.js'
s = open(p, encoding='utf-8', errors='replace').read()
seg = s[2719500:2728000]
io.open(r'D:\scan\figma_report\_ah2_module_dump.txt', 'w', encoding='utf-8').write(seg)
print('dumped', len(seg))

# 另:toQueryParameters 定义
import re
out2 = []
for m in re.finditer(r'toQueryParameters', s):
    a, b = max(0, m.start()-200), min(len(s), m.end()+300)
    out2.append('===== toQueryParameters @%d =====' % m.start())
    out2.append(s[a:b])
io.open(r'D:\scan\figma_report\_ah2_toquery.txt', 'w', encoding='utf-8').write('\n'.join(out2))
print('toQueryParameters blocks:', len(out2))
