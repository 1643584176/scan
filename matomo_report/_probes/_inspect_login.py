# -*- coding: utf-8 -*-
import re

b = open(r'F:\scan\matomo_report\_probes\_login_page.html', encoding='utf-8', errors='replace').read()
# find nonce-ish attrs
for m in re.finditer(r'nonce[^>]{0,120}', b):
    print('NONCE-ATTR:', m.group(0)[:150])
    break
# vue root element attributes
i = b.find('piwik-app')
print('piwik-app at', i)
if i > 0:
    print(b[i - 200:i + 600])
# login form area
j = b.find('login')
print('login form context:')
k = b.find('login_name')
print('login_name at', k)
if k > 0:
    print(re.sub(r'\s+', ' ', b[k - 500:k + 500])[:900])
