# -*- coding: utf-8 -*-
import json, re
for ln in open(r'D:\scan\_run_v175_out.txt', encoding='utf-8', errors='replace'):
    try:
        o = json.loads(ln)
    except Exception:
        continue
    d = o.get('data', '')
    if isinstance(d, str) and ('TREE' in d or 'HANDLERS' in d):
        for seg in re.split(r'(?=\[\d+\.\d\] )', d):
            if 'TREE' in seg or 'HANDLERS' in seg or 'Mount' in seg and 'dst' in seg:
                print(seg[:1200])
