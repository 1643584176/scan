# -*- coding: utf-8 -*-
"""提取 v122 descriptor 输出"""
import re, io, sys

sys.stdout.reconfigure(encoding='utf-8')
txt = io.open('_run_v122_out.txt', encoding='utf-8', errors='replace').read()
# 提取所有 data 块
blobs = []
for m in re.finditer(r'"data":"((?:[^"\\]|\\.)*)"', txt):
    blobs.append(m.group(1).encode().decode('unicode_escape', errors='replace'))
blob = '\n'.join(blobs)
# 保存 descriptor 内容到文件
io.open('_v122d_local.txt', 'w', encoding='utf-8', errors='replace').write(blob)
# 打印关键统计 + celld 读取状态
for l in blob.splitlines():
    if any(k in l for k in ('celld', 'gzip blocks', 'descriptor output', '=== FILE', 'SVC vercel.hive.cell')):
        print(l[:300])
print('---total lines:', len(blob.splitlines()))
