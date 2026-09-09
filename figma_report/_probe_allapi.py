# -*- coding: utf-8 -*-
"""全量端点提取(161 chunk, n2i 方法论): 输出所有 /api/ 端点簇"""
import sys, io, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

JS = r'D:\scan\figma_report\_js'
files = ['figma_app-main.js'] + [f for f in os.listdir(JS) if f.endswith('.min.js')]
cnt = {}
for fn in files:
    try:
        data = open(os.path.join(JS, fn), encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    # url`...` 模板 + 字符串内 /api/ 路径
    for m in re.finditer(r'url`(/api/[^`]+)`', data):
        ep = re.sub(r'\$\{[^}]*\}', '{}', m.group(1))
        ep = re.sub(r'(/[a-z0-9_]+)\$\{[^}]*\}', r'\1{}', ep)
        cnt.setdefault(ep, []).append(fn)
    for m in re.finditer(r'["\x60](/api/[a-zA-Z0-9_/.\-${}]{4,90})["\x60]', data):
        ep = re.sub(r'\$\{[^}]*\}', '{}', m.group(1))
        cnt.setdefault(ep, []).append(fn)

seen = set()
for ep, fl in sorted(cnt.items(), key=lambda x: -len(x[1])):
    if ep in seen:
        continue
    seen.add(ep)
    print(f'{len(fl):3d}  {ep}')
print(f'TOTAL {len(seen)}')
print('ALL DONE')
