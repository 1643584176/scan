# -*- coding: utf-8 -*-
"""Read key action methods of Installation Controller."""
import re

p = r'F:\scan\matomo_report\_src\matomo-release\matomo\plugins\Installation\Controller.php'
src = open(p, encoding='utf-8', errors='replace').read()

# split by method
parts = re.split(r'\n    public function ', src)
for part in parts[1:]:
    name = part.split('(')[0]
    if name not in ('welcome', 'databaseSetup', 'tablesCreation', 'setupSuperUser',
                    'firstWebsiteSetup', 'finished', 'trackingCode', 'reuseTables'):
        continue
    body = part[:2600]
    print('=' * 25, name)
    print(body)
    print()
