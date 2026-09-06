# -*- coding: utf-8 -*-
import re

b = open(r'F:\scan\matomo_report\_probes\_su_post.html', encoding='utf-8', errors='replace').read()
t = re.search(r'<title>(.*?)</title>', b, re.S)
print('TITLE:', t.group(1)[:200] if t else 'none')
for m in re.finditer(r'<(?:h1|h2|h3)[^>]*>(.*?)</(?:h1|h2|h3)>', b, re.S)[:6]:
    print('H:', re.sub(r'<[^>]+>', '', m.group(1)).strip()[:200])
for kw in ['Thanks', 'Congrat', 'success', 'error', 'Error', 'login', 'password', 'Website', 'Tracking']:
    i = b.find(kw)
    if i >= 0:
        print(kw, 'at', i)
# alerts divs any class
for mm in re.finditer(r'<div class="[^"]*alert[^"]*">(.*?)</div>', b, re.S):
    print('ALERTDIV:', re.sub(r'<[^>]+>|\s+', ' ', mm.group(1)).strip()[:300])
# forms present?
print('forms:', re.findall(r'<form[^>]*>', b)[:2])
print('links:', sorted(set(re.findall(r'href="([^"]*)"', b)))[:10])
