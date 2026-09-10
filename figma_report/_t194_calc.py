# -*- coding: utf-8 -*-
# 计算 r194a P1a payload 的 @1:215 位置字符
import json
cid = '1f08ab7f-7e00-4696-a732-1cc44e9e9c19'
fid = 'e41ab925-cff7-4938-a801-91394f4cb302'
b = {'collection_id': cid, 'name': 'r194base-5ebf50', 'description': 'r194 desc base',
     'fields': [{'id': fid, 'name': 'r194f0', 'field_type': 'text', 'position': 0,
                 'required': False, 'properties': {}, 'role': None}]}
s = json.dumps(b)
print('total len:', len(s))
print('char@210..232:', repr(s[208:232]))
i = 215 - 1
print('char@215 exactly:', repr(s[i-2:i+9]))
# 逐 10 字符标注
for st in range(0, len(s), 50):
    print(f'{st+1:4d}: {s[st:st+50]}')
