# -*- coding: utf-8 -*-
"""Check HostPortExtractor + createDatabaseObject port handling."""
import re

p = r'F:\scan\matomo_report\_src\matomo-release\matomo\plugins\Installation\HostPortExtractor.php'
src = open(p, encoding='utf-8', errors='replace').read()
print(src[:4000])

p2 = r'F:\scan\matomo_report\_src\matomo-release\matomo\plugins\Installation\FormDatabaseSetup.php'
src2 = open(p2, encoding='utf-8', errors='replace').read()
i = src2.find('function createDatabaseObject')
print('=' * 20)
print(src2[i:i + 1800])
