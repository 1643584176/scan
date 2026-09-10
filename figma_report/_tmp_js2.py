# -*- coding: utf-8 -*-
import io, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
t = open('_js/935-431f89677a39072c.min.js', encoding='utf-8', errors='replace').read()
for kw in ('checkpoint_diff', 'migration_version'):
    print(f'##### [{kw}] #####')
    for m in re.finditer(re.escape(kw), t):
        a = max(0, m.start() - 700)
        b = min(len(t), m.end() + 500)
        print(f'--- @{m.start()} ---')
        print(t[a:b])
        print()
