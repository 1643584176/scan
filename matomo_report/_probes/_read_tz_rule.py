# -*- coding: utf-8 -*-
import re

p = r'F:\scan\matomo_report\_src\matomo-release\matomo\plugins\Installation\FormFirstWebsiteSetup.php'
src = open(p, encoding='utf-8', errors='replace').read()
i = src.find('class RuleIsValidTimezone')
print(src[i:i + 2500])
