# -*- coding: utf-8 -*-
import re

# 1) finished action code
p = r'F:\scan\matomo_report\_src\matomo-release\matomo\plugins\Installation\Controller.php'
src = open(p, encoding='utf-8', errors='replace').read()
i = src.find('function finished')
print('=== finished ===')
print(src[i:i + 2200])

# 2) isMatomoInstalled
p2 = r'F:\scan\matomo_report\_src\matomo-release\matomo\core\SettingsPiwik.php'
try:
    s2 = open(p2, encoding='utf-8', errors='replace').read()
    j = s2.find('function isMatomoInstalled')
    print('=== isMatomoInstalled ===')
    print(s2[j:j + 900])
except Exception as e:
    print('ERR', e)

# 3) config full
cfg = r'F:\scan\matomo_report\_src\matomo-release\matomo\config\config.ini.php'
print('=== config ===')
print(open(cfg, encoding='utf-8', errors='replace').read())
