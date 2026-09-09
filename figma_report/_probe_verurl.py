# -*- coding: utf-8 -*-
"""考古 main JS: version 保存/恢复/更新的 Ay.url 模板"""
import sys, io, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

JS = r'D:\scan\figma_report\_js'
main = os.path.join(JS, 'figma_app-main.js')
data = open(main, encoding='utf-8', errors='replace').read()

# 找 versions 相关 URL 模板(任意 method) + file_version / savepoint / checkpoint API 调用
pats = [r'Ay\.(?:get|post|put|del|patch)\([^)]{0,40}versions[^)]{0,120}\)',
        r'url`[^`]{0,100}(?:versions|checkpoint|savepoint)[^`]{0,80}`',
        r'(?:GET|POST|PUT|DELETE|PATCH)[^;]{0,30}/api/[^"\x60]{0,80}(?:version|checkpoint)[^"\x60]{0,40}']
seen = set()
for pat in pats:
    for m in list(re.finditer(pat, data)):
        frag = m.group(0)[:150]
        if frag in seen:
            continue
        seen.add(frag)
        s = max(0, m.start() - 200)
        e = min(len(data), m.end() + 150)
        print(f'PAT@ {m.start()}:')
        print(f'   {data[s:e][:400]}')
        print()
        if len(seen) > 30:
            print('TRUNCATED')
            print('ALL DONE')
            sys.exit(0)
print('ALL DONE')
