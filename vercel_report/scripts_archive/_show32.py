# -*- coding: utf-8 -*-
import json
txt = open('skills/out/vda32_celld_plugin_guest_20260830_132055.txt', encoding='utf-8').read()
for line in txt.splitlines():
    try:
        d = json.loads(line)
        if 'data' in d:
            print(d['data'])
    except Exception:
        pass
