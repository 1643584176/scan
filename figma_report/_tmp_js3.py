# -*- coding: utf-8 -*-
import io, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
t = open('_js/figma_app-main.js', encoding='utf-8', errors='replace').read()
print('##### [migration_version] in figma_app-main.js #####')
for m in re.finditer(re.escape('migration_version'), t):
    a = max(0, m.start() - 800)
    b = min(len(t), m.end() + 600)
    print(f'--- @{m.start()} ---')
    print(t[a:b])
    print()
