# -*- coding: utf-8 -*-
"""Read Installation.php (dispatch) fully + firstWebsiteSetup tail."""
import re

p = r'F:\scan\matomo_report\_src\matomo-release\matomo\plugins\Installation\Installation.php'
print(open(p, encoding='utf-8', errors='replace').read())

p2 = r'F:\scan\matomo_report\_src\matomo-release\matomo\plugins\Installation\Controller.php'
src = open(p2, encoding='utf-8', errors='replace').read()
i = src.find('function firstWebsiteSetup')
print('=' * 30)
print(src[i:i + 3000])
