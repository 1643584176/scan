# -*- coding: utf-8 -*-
"""Vercel 窗口收尾:根目录 770 个一次性实验脚本统一归档到 vercel_report/scripts_archive/
保留:非 _ 前缀的 py(核心工具)、所有非 py 文件"""
import os, shutil, sys

ROOT = r'D:\scan'
DST = os.path.join(ROOT, 'vercel_report', 'scripts_archive')
os.makedirs(DST, exist_ok=True)

# 保留在根目录的 py(核心/工具,非一次性实验)
KEEP = {
    '_analyze_v63.py', '_wh_create.py', '_fix_paths.py',
}
# 其余所有 _*.py 移动归档;无前缀 py 也检查是否一次性(vda*/atk*/celld*/chk* 等实验类)

moved, kept, skipped = [], [], []
for fn in sorted(os.listdir(ROOT)):
    if not fn.endswith('.py'):
        continue
    src = os.path.join(ROOT, fn)
    if fn in KEEP:
        kept.append(fn)
        continue
    # 实验类: _ 前缀 或 实验命名 (vda/atk/celld/chk/exp/fw/allowcmp/deny 等)
    low = fn.lower()
    if fn.startswith('_') or low.startswith(('vda', 'atk_', 'celld', 'chk', 'exp_', 'fw', 'allowcmp', 'deny', 'mmds', 'cidr', 'sb_', 'snap_')):
        dst = os.path.join(DST, fn)
        try:
            shutil.move(src, dst)
            moved.append(fn)
        except Exception as e:
            skipped.append((fn, str(e)))
    else:
        kept.append(fn)

print('moved=%d kept=%d skipped=%d' % (len(moved), len(kept), len(skipped)))
print('--- kept ---')
for f in kept:
    print(' ', f)
if skipped:
    print('--- skipped ---')
    for f, e in skipped:
        print(' ', f, e)
