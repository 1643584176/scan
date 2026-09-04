# -*- coding: utf-8 -*-
"""找 prod_app.js 首个 import{ 的 from 结尾"""
import re, os

here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, '_js', 'prod_app.js'), encoding='utf-8', errors='replace').read()
out = []
# 找所有 import 块 from"./xxx.js" 且前面的 bind 含 ag as so
for m in re.finditer(r'import\{[^}]*\bso\b[^}]*\}from"[^"]+"', src):
    out.append('MATCH len=%d head=%s tail=%s' % (len(m.group(0)), m.group(0)[:200], m.group(0)[-120:]))
# 备选: 所有 import{...}from 行(短于 2000 字符的)
for m in re.finditer(r'import\{[^}]{0,3000}\}from"\./[A-Za-z0-9_\-]+\.js"', src):
    s = m.group(0)
    if len(s) < 1200:
        out.append('SHORT-IMPORT tail: ' + s[-150:])
open(os.path.join(here, '_p61_out.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('done lines:', len(out), flush=True)
