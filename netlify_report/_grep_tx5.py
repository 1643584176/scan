# -*- coding: utf-8 -*-
import json

f = open(r'C:\Users\tndc2\.qoder\cache\projects\scan-72ece876\conversation-history\92f41401\92f41401.jsonl',
         encoding='utf-8', errors='replace')
lines = f.readlines()
# 看第 6 条消息的完整结构(role=user 的)
for i in range(0, min(30, len(lines))):
    try:
        o = json.loads(lines[i])
    except Exception as e:
        continue
    print('LINE', i, 'role=', o.get('role'), 'keys=', list(o.keys()))
    c = o.get('message', {})
    print('  msg keys:', list(c.keys()))
    content = c.get('content')
    if isinstance(content, list):
        for j, x in enumerate(content):
            if isinstance(x, dict):
                print('  block', j, 'type=', x.get('type'), 'len=', len(str(x.get('text', '')))[:10], 'head=', str(x.get('text', ''))[:80].replace('\n', ' '))
