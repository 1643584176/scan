# -*- coding: utf-8 -*-
import json, re
for ln in open(r'D:\scan\_run_v177_out.txt', encoding='utf-8', errors='replace'):
    try:
        o = json.loads(ln)
    except Exception:
        continue
    d = o.get('data', '')
    if isinstance(d, str) and 'pwn out' in d:
        i = d.find('pwn out')
        print(d[max(0, i - 200):i + 2500])
