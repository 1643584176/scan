# -*- coding: utf-8 -*-
import re

b = open(r'F:\scan\matomo_report\_probes\_install_0.html', encoding='utf-8', errors='replace').read()
t = re.search(r'<title>(.*?)</title>', b, re.S)
print('TITLE:', t.group(1).strip()[:300] if t else 'none')
for m in re.findall(r'<(?:h1|h2|h3)[^>]*>(.*?)</(?:h1|h2|h3)>', b, re.S)[:10]:
    print('H:', re.sub(r'<[^>]+>', '', m).strip()[:200])
for kw in ['install', 'Install', 'System Check', 'database', 'exception', 'Not installed']:
    i = b.find(kw)
    print(kw, '->', i)
