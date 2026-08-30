# -*- coding: utf-8 -*-
import re, os
D = r'F:\scan\_sdk\package\dist'
files = ['sandbox.cjs', 'session.cjs', 'api-client/api-client.cjs', 'snapshot.cjs', 'command.cjs', 'filesystem.cjs']
pat = re.compile(r"['\"](/v[0-9]/[a-zA-Z0-9_{}\$\.\-\/]+)['\"]")
for f in files:
    p = os.path.join(D, f)
    s = open(p, encoding='utf-8', errors='replace').read()
    paths = sorted(set(pat.findall(s)))
    print('== %s' % f)
    for x in paths:
        print('  ', x)
