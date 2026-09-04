# -*- coding: utf-8 -*-
"""列 swagger 所有 function/edge/bundle 相关 operationId"""
import re
txt = open(r'D:\scan\netlify_report\_openapi\swagger.yml', encoding='utf-8').read()
for m in re.finditer(r'operationId: (\w+)', txt):
    op = m.group(1)
    if re.search(r'function|bundle|upload|deploy', op, re.I):
        print(op)
