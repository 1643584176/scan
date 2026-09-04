# -*- coding: utf-8 -*-
import re, io

txt = io.open('_run_v101_out.txt', encoding='utf-8', errors='replace').read()
# 提取所有 data 字段内容并解码
seen = set()
for m in re.finditer(r'"data":"((?:[^"\\]|\\.)*)"', txt):
    d = m.group(1).encode().decode('unicode_escape', errors='replace')
    key = d[:60]
    if key in seen:
        continue
    seen.add(key)
    if any(k in d for k in ('virtio', 'mknod', '/dev/mem', 'mmap', 'SBC', 'PID 535', 'DDAgent', 'VSOCK 1025', 'L1 ', 'L2 ', 'L3 ', 'L4 ', 'L5 ')):
        print(d[:1800])
        print('======')
