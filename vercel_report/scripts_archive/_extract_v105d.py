# -*- coding: utf-8 -*-
"""提取 v105 p3 文件完整内容到本地"""
import re, io

txt = io.open('_run_v105_out.txt', encoding='utf-8', errors='replace').read()
chunks = []
for m in re.finditer(r'"data":"((?:[^"\\]|\\.)*)"', txt):
    d = m.group(1).encode().decode('unicode_escape', errors='replace')
    # 只收集 p3 文件段 (以 K / GRPC / PROTO / SVCTYPE / PKG 开头的行)
    lines = [l for l in d.splitlines() if l.startswith(('K ', 'GRPC ', 'PROTO ', 'SVCTYPE ', 'PKG '))]
    if lines:
        chunks.extend(lines)
out = io.open('_v105p3_local.txt', 'w', encoding='utf-8')
seen = set()
for l in chunks:
    if l not in seen:
        seen.add(l)
        out.write(l + '\n')
out.close()
print('unique lines:', len(seen))
# 统计各类
from collections import Counter
c = Counter(l.split(' ')[0] for l in seen)
print(c)
