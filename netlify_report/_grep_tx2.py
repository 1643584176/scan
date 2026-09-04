# -*- coding: utf-8 -*-
import json

f = open(r'C:\Users\tndc2\.qoder\cache\projects\scan-72ece876\conversation-history\92f41401\92f41401.jsonl',
         encoding='utf-8', errors='replace')
lines = f.readlines()
cnt = 0
for i, ln in enumerate(lines):
    try:
        o = json.loads(ln)
    except Exception:
        continue
    if o.get('role') != 'user':
        continue
    try:
        msg = o['message']['content']
    except Exception:
        continue
    s = json.dumps(msg, ensure_ascii=False)
    # 找 user_query 标记
    if 'user_query' in s or '<user_query>' in s:
        cnt += 1
        print('LINE', i, '|', s[:300])
        print('=====')
        if cnt > 40:
            break
print('total user_query hits:', cnt)
