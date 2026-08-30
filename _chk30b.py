# -*- coding: utf-8 -*-
import json, re
txt = open('_run_v30q_out.txt', encoding='utf-8', errors='replace').read()
# 找第一个 data 字段完整内容
for m in re.finditer(r'\{"data":"(.*?)","stream":"stdout"\}', txt, re.S):
    try:
        d = json.loads('"' + m.group(1) + '"')
        print(d[:3500])
        print('===END==='.center(60, '='))
    except Exception as e:
        print('parse err', e, repr(m.group(1)[:200]))
    break
