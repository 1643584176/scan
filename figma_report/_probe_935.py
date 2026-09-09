# -*- coding: utf-8 -*-
"""考古 935 chunk: save_local_copy 真实端点 + 下载 .fig 的权限检查"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

data = open(r'D:\scan\figma_report\_js\935-431f89677a39072c.min.js', encoding='utf-8', errors='replace').read()
print('len', len(data))

for kw in ['save_local_copy', 'copy_to_local', 'local_copy', 'canExport', 'viewer_export', 'fig', 'download']:
    ms = list(re.finditer(kw, data))
    print(f'===== [{kw}] x{len(ms)} =====')
    for m in ms[:10]:
        s = max(0, m.start() - 300)
        e = min(len(data), m.end() + 300)
        print(f'@{m.start()}: {data[s:e].replace(chr(10)," ")[:620]}')
        print()
print('ALL DONE')
