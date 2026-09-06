# -*- coding: utf-8 -*-
"""Locate genericForm.twig + installation layout form handling."""
import os

root = r'F:\scan\matomo_report\_src\matomo-release\matomo'
hits = []
for base, dirs, files in os.walk(root):
    for f in files:
        if f == 'genericForm.twig':
            hits.append(os.path.join(base, f))
for h in hits:
    print(h)
    print(open(h, encoding='utf-8', errors='replace').read()[:2500])
    print('-----')
