# -*- coding: utf-8 -*-
import json
for ln in open(r'D:\scan\_run_v178_out.txt', encoding='utf-8', errors='replace'):
    try:
        o = json.loads(ln)
    except Exception:
        continue
    d = o.get('data', '')
    if isinstance(d, str) and 'PWN +' in d:
        i = d.find('PWN +')
        print(d[i:i + 4500])
        print('=' * 60)
