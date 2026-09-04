# -*- coding: utf-8 -*-
import glob, re
hits = []
for f in glob.glob('*.py'):
    try:
        src = open(f, encoding='utf-8', errors='ignore').read()
    except Exception:
        continue
    for m in re.finditer(r'.*(auth/token|/token|jwks).*', src):
        line = m.group(0).strip()
        hits.append((f, line[:140]))
for f, line in hits[:60]:
    print('%s: %s' % (f, line))
