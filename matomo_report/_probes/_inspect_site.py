# -*- coding: utf-8 -*-
import re

b = open(r'F:\scan\matomo_report\_probes\_site_post.html', encoding='utf-8', errors='replace').read()
t = re.search(r'<h2>(.*?)</h2>', b, re.S)
print('H2:', t.group(1)[:150] if t else 'none')
for mm in re.finditer(r'<div class="alert alert-(danger|warning)">(.*?)</div>', b, re.S):
    print('ALERT', mm.group(1), ':', re.sub(r'<[^>]+>|\s+', ' ', mm.group(2)).strip()[:500])
# forms?
fm = re.search(r'<form\b[^>]*>', b)
print('FORM:', fm.group(0)[:200] if fm else 'NONE')
if fm:
    end = b.find('</form>', fm.end())
    seg = b[fm.end():end]
    for m in re.finditer(r'<(?:input|select)\b[^>]*>', seg):
        t2 = m.group(0)
        nm = re.search(r'name="([^"]*)"', t2)
        val = re.search(r'value="([^"]*)"', t2)
        print('  ', (nm.group(1) if nm else '?'), '=', (val.group(1)[:40] if val else ''), t2[:90])
