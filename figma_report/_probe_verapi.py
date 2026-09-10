# -*- coding: utf-8 -*-
"""考古 file version 创建/恢复 REST 端点 URL: main JS + 相关 chunk 里 versions API 调用形态"""
import sys, io, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

JS = r'D:\scan\figma_report\_js'
files = ['figma_app-main.js'] + [f for f in os.listdir(JS) if f.endswith('.min.js')]
print(f'total files: {len(files)}')

# 1. URL 模板形态: /api/versions /versions/ 的 POST/PUT/DELETE 调用
url_pats = [r'url`\s*[/]?api/versions[^`]*`', r'`[/]api/versions[^`]*`',
            r'"[/]api/versions[^"]*"', r"'[/]api/versions[^']*'",
            r'url`[^`]*file_versions[^`]*`', r'/v1/files/[^"`\s]{0,40}/versions']
seen = set()
for fn in files:
    p = os.path.join(JS, fn)
    try:
        data = open(p, encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    for pat in url_pats:
        for m in re.finditer(pat, data):
            frag = m.group(0)[:200]
            key = (fn, frag)
            if key in seen:
                continue
            seen.add(key)
            s = max(0, m.start() - 120)
            e = min(len(data), m.end() + 120)
            print(f'=== {fn} {pat[:25]}:')
            print(f'   {data[s:e][:320]}')
            print()
            if len(seen) > 40:
                print('TRUNCATED')
                print('ALL DONE')
                sys.exit(0)
print('ALL DONE')
