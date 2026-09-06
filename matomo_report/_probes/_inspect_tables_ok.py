# -*- coding: utf-8 -*-
import re

b = open(r'F:\scan\matomo_report\_probes\_db_post2.html', encoding='utf-8', errors='replace').read()
# links & forms
print('FORMS:', re.findall(r'<form[^>]*>', b)[:3])
print('LINKS:', sorted(set(re.findall(r'href="([^"]*)"', b)))[:15])
# js api calls
for m in re.finditer(r'(?:ajax|API|api|fetch|XMLHttpRequest)[^;]{0,120}', b[:200000]):
    pass
print('ACTION refs:', sorted(set(re.findall(r'action=([\w]+)', b)))[:20])
# any meta refresh / auto submit
print('auto:', bool(re.search(r'<meta[^>]*refresh', b, re.I)))
# look for table list already created in the html
print('has matomo_ tables text:', b.count('matomo_'))
