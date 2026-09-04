# -*- coding: utf-8 -*-
"""v105 P3 探测结果 + p3 文件内容"""
import re, io

txt = io.open('_run_v105_out.txt', encoding='utf-8', errors='replace').read()
chunks = []
for m in re.finditer(r'"data":"((?:[^"\\]|\\.)*)"', txt):
    chunks.append(m.group(1).encode().decode('unicode_escape', errors='replace'))
blob = '\n'.join(chunks)
# P3 部分
i = blob.find('=== P3 selected probes ===')
j = blob.find('V105C_DONE')
seg = blob[i:j if j > i else i + 20000]
lines = [l for l in seg.splitlines() if l.strip()]
for l in lines:
    print(l[:220])
print('...')
# p3 文件内容(驱动 [p3 file] 段)
k = blob.find('[p3 file]')
if k > 0:
    print('==== P3 FILE ====')
    print(blob[k:k + 90000][:90000])
