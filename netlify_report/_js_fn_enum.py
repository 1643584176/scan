# -*- coding: utf-8 -*-
"""枚举 _js bundle 中所有 /.netlify/functions/ 函数名(找 database-query 同族)"""
import re, os, glob

base = r'D:\scan\netlify_report\_js'
names = {}
for f in glob.glob(os.path.join(base, '*.js')) + glob.glob(os.path.join(base, '*.html')):
    try:
        d = open(f, encoding='utf-8', errors='ignore').read()
    except Exception:
        continue
    for m in re.finditer(r'/\.netlify/functions/([A-Za-z0-9_-]+)', d):
        names.setdefault(m.group(1), set()).add(os.path.basename(f))

for n in sorted(names):
    print('%-40s %s' % (n, ','.join(sorted(names[n]))))
