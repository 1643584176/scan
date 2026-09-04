# -*- coding: utf-8 -*-
"""解析 v123: 提取区域文件列表和读取状态"""
import re, io, sys

sys.stdout.reconfigure(encoding='utf-8')
txt = io.open('_run_v123_out.txt', encoding='utf-8', errors='replace').read()
# 区域列表
for m in re.finditer(r'target .*?-> v123d_\d+\.bin \(\d+B\)|total regions=\d+|\[regions count\] \d+', txt):
    print(m.group(0))
# 检查关键内容是否出现 (ExecRequest 附近应有字段名)
blobs = []
for m in re.finditer(r'"data":"((?:[^"\\]|\\.)*)"', txt):
    blobs.append(m.group(1).encode().decode('unicode_escape', errors='replace'))
blob = '\n'.join(blobs)
io.open('_v123d_local.bin', 'wb').write(blob.encode('utf-8', errors='replace'))
print('--- blobs saved, total chars:', len(blob))
for kw in ('process_id', 'output_stream', 'container_id', 'args', 'ExecProcess', 'MSG '):
    print(kw, ':', blob.count(kw))
