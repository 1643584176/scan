"""宽松提取所有 JS 中的 API 路径（/vN/、/api/、REST 风格）"""
import re, glob, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

pat = re.compile(r'["\'](/(?:v\d+|api|rest|internal|auth|user|account|session|order|cart|store|delivery|address|payment|signup|login|verify|register|onboarding)[a-zA-Z0-9_\-/\.{}]*)["\']')
eps = {}
for f in glob.glob('js/*.js'):
    src = open(f, encoding='utf-8', errors='replace').read()
    for m in pat.finditer(src):
        u = m.group(1)
        if len(u) > 5 and 'graphql' not in u:
            eps.setdefault(u, 0)
            eps[u] += 1

print(f'共 {len(eps)} 个路径')
for e in sorted(eps, key=lambda x: -eps[x]):
    print(f'  x{eps[e]:<3} {e}')
