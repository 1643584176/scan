# -*- coding: utf-8 -*-
import glob, re
pats = [r'.*(/token|get-token|new-token|issue).*', r'.*neonauth.*']
for f in sorted(glob.glob('_j*.py')) + sorted(glob.glob('_k*.py')) + sorted(glob.glob('_m*.py')):
    try:
        src = open(f, encoding='utf-8', errors='ignore').read()
    except Exception:
        continue
    for m in re.finditer(pats[0], src):
        line = m.group(0).strip()
        if 'token' in line.lower() and ('/token' in line or 'auth/token' in line or 'get-token' in line):
            print('%s: %s' % (f, line[:150]))
