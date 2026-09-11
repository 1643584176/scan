# -*- coding: utf-8 -*-
"""1) 找 r129-r144 运行时段; 2) 全会话扫 checkpoint_diff 输出; 3) 今日总结 checkpoint 上下文"""
import io, os

FIG = r'D:/scan/figma_report'
BASE = r'C:/Users/tndc2/.qoder/cache/projects/scan-72ece876/conversation-history'

print('===== 1. 脚本 mtime =====')
for fn in ['_figma_r129.py', '_figma_r133.py', '_figma_r135.py', '_figma_r136.py',
           '_figma_r137.py', '_figma_r139.py', '_figma_r142.py', '_figma_r144_clean.py']:
    p = os.path.join(FIG, fn)
    if os.path.exists(p):
        import time as T
        print('%-24s %s' % (fn, T.strftime('%m-%d %H:%M', T.localtime(os.path.getmtime(p)))))

print()
print('===== 2. 会话扫描 checkpoint_diff =====')
for d in sorted(os.listdir(BASE)):
    dp = os.path.join(BASE, d)
    if not os.path.isdir(dp):
        continue
    for fn in os.listdir(dp):
        if not fn.endswith('.jsonl'):
            continue
        txt = io.open(os.path.join(dp, fn), encoding='utf-8', errors='ignore').read()
        c1, c2 = txt.count('checkpoint_diff'), txt.count('from_file_version_id')
        if c1 or c2:
            print('%-10s checkpoint_diff=%d from_fv=%d' % (d, c1, c2))

print()
print('===== 3. 今日总结 checkpoint 行 =====')
p = os.path.join(FIG, 'Figma-今日总结-2026-09-10.md')
txt = io.open(p, encoding='utf-8', errors='ignore').read()
for i, ln in enumerate(txt.split('\n')):
    if 'checkpoint' in ln or 'file_diff' in ln or '未测' in ln:
        print('%4d| %s' % (i + 1, ln.strip()[:200]))
