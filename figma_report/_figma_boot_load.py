# -*- coding: utf-8 -*-
"""INITIAL_OPTIONS 中 livegraph/view/entry 字段 + bootstrap 中主 bundle 加载逻辑"""
import re

c = open('D:/scan/figma_report/_js/app_file.html', 'r', encoding='utf-8', errors='ignore').read()
scripts = re.findall(r'<script(?![^>]*src)[^>]*>(.*?)</script>', c, re.S)
io = scripts[3]  # INITIAL_OPTIONS

print('== INITIAL_OPTIONS livegraph/view 相关 ==')
for kw in ['livegraph', 'preload_view', 'entrypoint', 'webpack', 'figma_app', 'bundle', 'runtime']:
    for m in list(re.finditer(r'.{60}%s.{80}' % kw, io))[:6]:
        print(' [%s]:' % kw, m.group(0).replace('\n', ' ')[:160])

print()
print('== bootstrap 中的 .min.js 加载逻辑 ==')
for fname in ['935-431f89677a39072c.min.js', 'auth-61211038b210d6ec.min.js',
              'vendor-core-ff6ab2ad5ffa3e30.min.js', 'vendor-3871c33a541abc9e.min.js']:
    d = open('D:/scan/figma_report/_js/' + fname, 'r', encoding='utf-8', errors='ignore').read()
    hits = list(re.finditer(r'.{50}[a-z0-9_~]+-[0-9a-f]{8,}\.min\.js.{30}', d))
    print(fname, 'min.js refs:', len(hits))
    for m in hits[:12]:
        print('   ', m.group(0).replace('\n', ' ')[:140])
