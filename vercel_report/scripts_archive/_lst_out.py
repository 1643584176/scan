# -*- coding: utf-8 -*-
"""列出 out 目录文件(按修改时间倒序), 可选关键字过滤"""
import os, sys
sys.stdout.reconfigure(encoding='utf-8')

d = r'F:\scan\skills\out'
kws = sys.argv[1:] if len(sys.argv) > 1 else []
for f in sorted(os.listdir(d), key=lambda x: os.path.getmtime(os.path.join(d, x)), reverse=True):
    if not kws or any(k in f for k in kws):
        print('%s  %s' % (f, os.path.getmtime(os.path.join(d, f))))
