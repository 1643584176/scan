# -*- coding: utf-8 -*-
import re

p2 = r'F:\scan\matomo_report\_src\matomo-release\matomo\plugins\Installation\Controller.php'
src = open(p2, encoding='utf-8', errors='replace').read()
for name in ['redirectToNextStep', 'checkPiwikIsNotInstalled', 'checkInstallationIsNotExpired',
             'getInstallationSteps', 'createConfigFile', 'getParam']:
    i = src.find('function ' + name)
    if i < 0:
        print('MISS', name)
        continue
    print('=' * 25, name)
    print(src[i:i + 1500])
