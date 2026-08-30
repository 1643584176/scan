# -*- coding: utf-8 -*-
import json
try:
    txt = open('skills/out/vda30_ctrd_deep_guest_20260830_130500.txt', encoding='utf-8').read()
    for line in txt.splitlines():
        try:
            d = json.loads(line)
            if 'data' in d:
                print(d['data'])
        except Exception:
            pass
except Exception as e:
    print('ERR', e)
