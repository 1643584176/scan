# -*- coding: utf-8 -*-
"""收尾: 归档脚本自身 + 残留 bin 移入 scripts_archive"""
import os, shutil

dst = r'D:\scan\vercel_report\scripts_archive'
for f in ['_archive_scripts.py', '_archive_outputs.py', '_v123d_local.bin']:
    src = os.path.join(r'D:\scan', f)
    try:
        shutil.move(src, os.path.join(dst, f))
        print('moved', f)
    except Exception as e:
        print('skip', f, e)
