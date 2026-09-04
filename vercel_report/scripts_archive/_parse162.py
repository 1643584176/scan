# -*- coding: utf-8 -*-
import json, re
data = open(r'D:\scan\_run_v162_out.txt', encoding='utf-8', errors='replace').read()
seen = set()
for m in re.finditer(r'"data":"(.*?)","stream"', data):
    s = m.group(1).replace('\\n', '\n').replace('\\"', '"')
    for ln in s.splitlines():
        if ln not in seen:
            seen.add(ln)
            print(ln[:500])
