# -*- coding: utf-8 -*-
"""全量扫描: checkpoint id 字段 + file_diff 调用点"""
import os, io

FIG = r'D:/scan/figma_report'
PATS = ['file_diff/v2', 'from_file_version_id', 'checkpointId', 'checkpoint_id',
        'branch_checkpoint', 'last_checkpoint', 'checkpoints']

print('===== A. 顶层全扩展名扫描 =====')
for fn in sorted(os.listdir(FIG)):
    fp = os.path.join(FIG, fn)
    if not os.path.isfile(fp):
        continue
    if fn.endswith(('.py', '.md', '.txt', '.json', '.html')):
        pass
    try:
        if os.path.getsize(fp) > 30 * 1024 * 1024:
            continue
        txt = io.open(fp, encoding='utf-8', errors='ignore').read()
    except Exception:
        continue
    hits = {p: txt.count(p) for p in PATS if txt.count(p)}
    if hits:
        print('%-55s %s' % (fn, hits))
