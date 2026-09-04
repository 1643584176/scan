# -*- coding: utf-8 -*-
import json, re
seen = set()
out = []
for ln in open(r'D:\scan\_run_v182_out.txt', encoding='utf-8', errors='replace'):
    try:
        o = json.loads(ln)
    except Exception:
        continue
    d = o.get('data', '')
    if isinstance(d, str):
        for m in re.finditer(r'\[\d+\.\d\] ([^\n]+)', d):
            s = m.group(1)
            if s not in seen:
                seen.add(s)
                out.append(s[:4000])
open(r'D:\scan\_v182_view.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('lines=%d' % len(out))
