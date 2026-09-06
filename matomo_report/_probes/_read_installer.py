# -*- coding: utf-8 -*-
"""List public actions in Installation controller + form fields."""
import os
import re

base = r'F:\scan\matomo_report\_src\matomo-release\matomo\plugins\Installation'
for fn in ['Controller.php', 'Installation.php', 'FormDatabaseSetup.php',
           'FormSuperUser.php', 'FormFirstWebsiteSetup.php', 'FormDefaultSettings.php']:
    p = os.path.join(base, fn)
    if not os.path.exists(p):
        print('MISSING', fn)
        continue
    src = open(p, encoding='utf-8', errors='replace').read()
    print('=' * 20, fn, len(src))
    for m in re.finditer(r'public function (\w+)\(', src):
        print('  action:', m.group(1))
    for m in re.finditer(r"action\s*=\s*'([^']+)'", src):
        print('  const action:', m.group(1))
    for m in re.finditer(r"method\s*=\s*'([^']+)'|createElement\('input',\s*\{?\s*name:\s*'([^']+)'|name:\s*'([^']+)'", src):
        print('  field?:', m.groups())
