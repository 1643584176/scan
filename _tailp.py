# -*- coding: utf-8 -*-
import json, sys
fn = sys.argv[1]
txt = open(fn, encoding='utf-8').read()
for line in txt.splitlines():
    try:
        d = json.loads(line)
        data = d.get('data', '')
        if data:
            print(data[-1500:])
    except Exception:
        pass
