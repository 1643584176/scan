# -*- coding: utf-8 -*-
import json, sys
txt = open('skills/out/vda27_ctrd_probe_guest_20260830_124920.txt', encoding='utf-8').read()
for line in txt.splitlines():
    try:
        d = json.loads(line)
        if 'data' in d:
            print(d['data'])
    except Exception:
        pass
