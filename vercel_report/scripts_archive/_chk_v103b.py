# -*- coding: utf-8 -*-
"""检查 v103 输出中 N1 strings 提取的实际内容"""
import re, io

txt = io.open('_run_v103_out.txt', encoding='utf-8', errors='replace').read()
chunks = []
for m in re.finditer(r'"data":"((?:[^"\\]|\\.)*)"', txt):
    chunks.append(m.group(1).encode().decode('unicode_escape', errors='replace'))
blob = '\n'.join(chunks)
# N1 部分: 找 sandbox.Controller / spawn / socket 相关行
kws = ['sandbox.Controller', 'spawn', 'Controller', '23456', 'vsock', 'Processes', 'SpawnService']
for kw in kws:
    n = blob.count(kw)
    print('%-20s %d' % (kw, n))
print('total chars:', len(blob))
# 打印包含 sandbox.Controller 的行
for ln in blob.splitlines():
    if 'Controller' in ln and len(ln) < 300:
        print('CTRL:', ln.strip()[:250])
        break
