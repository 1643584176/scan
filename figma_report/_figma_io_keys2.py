# -*- coding: utf-8 -*-
"""INITIAL_OPTIONS/EARLY_ARGS 全量 key dump"""
import re, json

c = open('D:/scan/figma_report/_js/app_file.html', 'r', encoding='utf-8', errors='ignore').read()
scripts = re.findall(r'<script(?![^>]*src)[^>]*>(.*?)</script>', c, re.S)
io_raw = scripts[3]
data = json.loads(io_raw)
for top in ['EARLY_ARGS', 'INITIAL_OPTIONS']:
    d = data[top]
    print('==== %s (%d keys) ====' % (top, len(d)))
    for k in sorted(d.keys()):
        v = d[k]
        vs = json.dumps(v, ensure_ascii=False)
        print('  %-46s = %s' % (k, vs[:120]))
    print()
