# -*- coding: utf-8 -*-
"""Read setupSuperUser + firstWebsiteSetup + redirectToNextStep + steps logic."""
import re

p = r'F:\scan\matomo_report\_src\matomo-release\matomo\plugins\Installation\Controller.php'
src = open(p, encoding='utf-8', errors='replace').read()
parts = re.split(r'\n    (?:public|protected|private) function ', src)
for part in parts[1:]:
    name = part.split('(')[0].split(' ')[-1].strip()
    if name in ('setupSuperUser', 'firstWebsiteSetup', 'redirectToNextStep',
                'getNextStep', 'isInstalled', 'checkPiwikIsNotInstalled',
                'createConfigFile', 'tablesCreation', 'finishInstallation'):
        print('=' * 25, name)
        print(part[:2200])
        print()
