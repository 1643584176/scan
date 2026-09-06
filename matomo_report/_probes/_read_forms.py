# -*- coding: utf-8 -*-
"""Extract form fields and POST target from installer classes/templates."""
import os
import re

base = r'F:\scan\matomo_report\_src\matomo-release\matomo\plugins\Installation'
# 1) Form classes: addElement(..., 'text', 'fieldname', ...)
for fn in ['FormDatabaseSetup.php', 'FormSuperUser.php', 'FormFirstWebsiteSetup.php']:
    src = open(os.path.join(base, fn), encoding='utf-8', errors='replace').read()
    print('=' * 15, fn)
    # find addElement calls: addElement('type', 'name', ...)
    for m in re.finditer(r"addElement\(\s*'(\w+)'\s*,\s*'(\w+)'", src):
        print('  elem:', m.groups())
    for m in re.finditer(r"setDefault\('(\w+)'", src):
        print('  default:', m.group(1))
    # table prefix default
    for m in re.finditer(r"tables_prefix[^;]{0,200}", src):
        print('  TBL:', re.sub(r'\s+', ' ', m.group(0))[:200])

# 2) templates: form action + hidden fields
tpl = os.path.join(base, 'templates')
for fn in os.listdir(tpl):
    p = os.path.join(tpl, fn)
    s = open(p, encoding='utf-8', errors='replace').read()
    acts = re.findall(r'action="([^"]+)"', s)
    if acts:
        print('TPL', fn, 'actions:', acts[:3])
        for m in re.finditer(r'<form[^>]*>', s):
            print('   form:', m.group(0)[:250])
