# -*- coding: utf-8 -*-
import re

p2 = r'F:\scan\matomo_report\_src\matomo-release\matomo\plugins\Installation\Controller.php'
src = open(p2, encoding='utf-8', errors='replace').read()
i = src.find('function firstWebsiteSetup')
print(src[i:i + 2600])
print('=' * 30)
# also: how welcome view + error message connect
j = src.find('function welcome')
print(src[j:j + 1200])
