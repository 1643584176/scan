# -*- coding: utf-8 -*-
"""查 v107 exec_probe 输出中 /run/cell 权限"""
import re, io

txt = io.open('_run_v107_out.txt', encoding='utf-8', errors='replace').read()
chunks = []
for m in re.finditer(r'"data":"((?:[^"\\]|\\.)*)"', txt):
    chunks.append(m.group(1).encode().decode('unicode_escape', errors='replace'))
blob = '\n'.join(chunks)
i = blob.find('[probe out]')
seg = blob[i:i + 6000]
for ln in seg.splitlines():
    if 'cell' in ln or 'sock' in ln or 'run/' in ln or 'CELL' in ln or '=== CELL' in ln or '=== RUN' in ln:
        print(ln[:200])
