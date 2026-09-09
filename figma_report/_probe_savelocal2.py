# -*- coding: utf-8 -*-
"""考古2: Save local copy 菜单 action (i18n key + action 注册 + 端点)"""
import sys, io, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

JS = r'D:\scan\figma_report\_js'
files = ['figma_app-main.js'] + sorted(f for f in os.listdir(JS) if f.endswith('.min.js'))

# i18n key 形态: xxx.save_local_copy / save_a_local_copy / local_copy 等
pats = [
    r'[a-z_]+\.(?:save[a-z_]*local[a-z_]*copy|local[a-z_]*copy[a-z_]*|save[a_z]*copy)',
    r'"(?:Save a local copy|Save local copy|Save a copy)[^"]*"',
    r"'(?:Save a local copy|Save local copy|Save a copy)[^']*'",
]
hits = {}
for fn in files:
    try:
        d = open(os.path.join(JS, fn), encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    for p in pats:
        for m in list(re.finditer(p, d)):
            frag = d[max(0, m.start()-160):m.end()+260].replace('\n', ' ')
            key = frag[:80]
            if key in hits:
                continue
            hits[key] = (fn, m.group(0)[:60], frag[:430])
for k, (fn, g0, frag) in list(hits.items())[:25]:
    print(f'--- {fn} [{g0}]')
    print(f'    {frag}')
    print()
print('total', len(hits))
print('ALL DONE')
