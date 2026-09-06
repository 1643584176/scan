# -*- coding: utf-8 -*-
p = r'F:\scan\matomo_report\_src\matomo-release\matomo\config\config.ini.php'
raw = open(p, 'rb').read()
print('bytes:', len(raw))
print(raw.decode('utf-8', 'replace'))
