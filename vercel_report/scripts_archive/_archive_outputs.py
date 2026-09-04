# -*- coding: utf-8 -*-
"""Vercel 收尾 v2: 根目录实验输出(_*.txt/v*.txt/v*_run.log 等)归档到 scripts_archive/outputs/
保留: vercel_cookies.txt(gitignore 已排除)、_wh_uuid.txt、目录、知识库文件"""
import os, shutil

ROOT = r'D:\scan'
DST = os.path.join(ROOT, 'vercel_report', 'scripts_archive', 'outputs')
os.makedirs(DST, exist_ok=True)

# 保留在根目录的文件(精确名)
KEEP_FILES = {'vercel_cookies.txt', '_wh_uuid.txt', 'F:scan_create_doc_parse.txt'}
# 保留目录
KEEP_DIRS = {'vercel_report', 'skills', 'figma_report', 'wolt_report', '_sdk',
             '经验', '模板.md', '__pycache__', '.idea', '.venv', '.git'}

moved, kept = [], []
for fn in sorted(os.listdir(ROOT)):
    p = os.path.join(ROOT, fn)
    if os.path.isdir(p):
        continue
    if fn in KEEP_FILES:
        kept.append(fn)
        continue
    # 实验输出特征: _*.txt / v*_run.log / v*.txt / _*.log
    low = fn.lower()
    if (fn.startswith('_') and fn.endswith('.txt')) or \
       (fn.startswith('_') and fn.endswith('.log')) or \
       (low.startswith('v') and (low.endswith('.txt') or low.endswith('.log'))):
        try:
            shutil.move(p, os.path.join(DST, fn))
            moved.append(fn)
        except Exception as e:
            kept.append('%s (%s)' % (fn, e))
    else:
        kept.append(fn)

print('moved=%d kept=%d' % (len(moved), len(kept)))
print('--- kept ---')
for f in kept:
    print(' ', f)
