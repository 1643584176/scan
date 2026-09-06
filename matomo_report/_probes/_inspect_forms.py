# -*- coding: utf-8 -*-
import re

b = open(r'F:\scan\matomo_report\_probes\_install_0.html', encoding='utf-8', errors='replace').read()
# find all forms
for i, fm in enumerate(re.finditer(r'<form[^>]*>', b)):
    print('FORM', i, ':', fm.group(0)[:300])
# find inputs with name anywhere
names = re.findall(r'<input[^>]*name="([^"]+)"[^>]*>', b)
print('input names:', sorted(set(names))[:40])
# look for action=... postTo etc
for pat in [r'action="([^"]*)"', r"action='([^']*)'", r'data-url="([^"]*)"', r'href="index\.php[^"]*"']:
    m = re.findall(pat, b)
    print(pat, '=>', sorted(set(m))[:30])
# any "next step" link
for kw in ['Next', 'next', 'System Check']:
    i = b.find(kw)
    if i > 0:
        print('--- around', kw, '---')
        print(re.sub(r'\s+', ' ', b[i-200:i+400])[:500])
