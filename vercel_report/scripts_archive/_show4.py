# -*- coding: utf-8 -*-
import json
txt = open('skills/out/vda4_cell_enum_guest_20260830_113826.txt', encoding='utf-8').read()
for line in txt.splitlines():
    try:
        d = json.loads(line)
        if 'data' in d and ('sock' in d['data'] or 'run/' in d['data']):
            print(d['data'])
    except Exception:
        pass
