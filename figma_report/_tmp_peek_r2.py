# -*- coding: utf-8 -*-
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
j = json.load(open(r'D:\scan\figma_report\_r2_res_widget.json', encoding='utf-8'))
m = j['meta']
it = m[0]
print('ALL KEYS:')
for k in it.keys():
    v = it[k]
    if isinstance(v, (dict, list)):
        s = json.dumps(v, ensure_ascii=False)
        print(f'  {k}: {s[:220]}')
    else:
        print(f'  {k}: {str(v)[:160]}')
print()
print('=== 数字长ID搜索 ===')
import re
s = json.dumps(it, ensure_ascii=False)
for mm in set(re.findall(r'"\d{15,20}"', s)):
    print('num-id-like:', mm)
# creator_id / user_id 字段
for k in ('creator_id', 'user_id', 'content_id', 'community_id', 'hub_file_id'):
    if k in it:
        print(f'{k} = {it[k]}')
