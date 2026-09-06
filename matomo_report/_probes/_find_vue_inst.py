# -*- coding: utf-8 -*-
"""Find how Vue installer submits database form."""
import os
import re

vue = r'F:\scan\matomo_report\_src\matomo-release\matomo\plugins\Installation\vue\src'
if not os.path.isdir(vue):
    # maybe compiled under dist
    for root, dirs, files in os.walk(r'F:\scan\matomo_report\_src\matomo-release\matomo\plugins\Installation'):
        for f in files:
            if f.endswith('.js') and 'dist' in root.lower():
                vue = root
                break
print('vue dir:', vue)
for root, dirs, files in os.walk(vue):
    for f in files:
        print(os.path.join(root, f))

# templates dir listing
tpl = r'F:\scan\matomo_report\_src\matomo-release\matomo\plugins\Installation\templates'
print('--- templates ---')
for f in os.listdir(tpl):
    print(f)
