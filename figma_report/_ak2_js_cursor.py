# -*- coding: utf-8 -*-
"""提取 query_timestamp / atob / decodeCursor / PaginatedQuery 的 JS 上下文"""
import re, io

p = r'D:\scan\figma_report\_js\figma_app-main.js'
s = open(p, encoding='utf-8', errors='replace').read()

out = []
for pat in [r'query_timestamp', r'atob\(', r'decodeCursor', r'fromCursor', r'parseCursor', r'PaginatedQuery']:
    out.append('########## PATTERN: %s ##########' % pat)
    n = 0
    for m in re.finditer(pat, s):
        n += 1
        if n > 12:
            out.append('... (more occurrences truncated)')
            break
        a, b = max(0, m.start()-220), min(len(s), m.end()+260)
        out.append('===== @%d =====' % m.start())
        out.append(s[a:b])
    if n == 0:
        out.append('(none)')

io.open(r'D:\scan\figma_report\_ak2_js_cursor.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('written', len(out), 'lines')
