# -*- coding: utf-8 -*-
"""分析 v104 输出: 每个 GRPC 请求耗时 + 确认 P1/P2 进度"""
import re, io

txt = io.open('_run_v104_out.txt', encoding='utf-8', errors='replace').read()
# 从 data 字段中解码出 guest 输出
chunks = []
for m in re.finditer(r'"data":"((?:[^"\\]|\\.)*)"', txt):
    d = m.group(1).encode().decode('unicode_escape', errors='replace')
    chunks.append(d)
blob = '\n'.join(chunks)
lines = [l for l in blob.splitlines() if l.startswith('[')]
print('total lines:', len(lines))
prev = None
for l in lines:
    m = re.match(r'\[(\d+\.\d)\]', l)
    if not m:
        continue
    t = float(m.group(1))
    if prev is not None:
        dt = t - prev
        if dt > 1.0:
            print('  +%.1fs  %s' % (dt, l[:120]))
        else:
            print('         %s' % l[:120])
    else:
        print('  start  %s' % l[:120])
    prev = t
