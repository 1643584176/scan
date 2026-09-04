# -*- coding: utf-8 -*-
"""列出 swagger 中 x-internal 端点路径"""
import re
txt = open(r'D:\scan\netlify_report\_openapi\swagger.yml', encoding='utf-8').read()
lines = txt.split('\n')
cur_path = None
cur_op = None
for i, ln in enumerate(lines):
    m = re.match(r'^  (/[^:]+):', ln)
    if m:
        cur_path = m.group(1)
    m2 = re.match(r'^    (get|post|put|delete|patch):', ln)
    if m2:
        cur_op = m2.group(1)
    if 'x-internal: true' in ln:
        print('%s [%s] line %d' % (cur_path, cur_op, i + 1))
