# -*- coding: utf-8 -*-
import re

b = open(r'F:\scan\matomo_report\_probes\_su_post.html', encoding='utf-8', errors='replace').read()
for kw in ['Super User', 'superuser', 'SuperUser', 'firstWebsiteSetup', 'created', 'Welcome', 'email', 'createSuperUser']:
    i = b.find(kw)
    if i >= 0:
        print('==', kw, 'at', i)
        print(re.sub(r'<[^>]+>|\s+', ' ', b[max(0, i - 150):i + 250])[:400])
# find the body/main content area
i = b.find('<body')
print('BODY at', i)
# look at the last 3000 chars of html for step markers
tail = b[-6000:]
print('TAIL:', re.sub(r'<[^>]+>|\s+', ' ', tail)[-800:])
